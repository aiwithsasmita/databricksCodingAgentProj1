#!/usr/bin/env python
# coding: utf-8

# # Graph RAG Demo with Hugging Face Embeddings
# 
# This notebook demonstrates a complete GraphRAG pipeline using:
# - **Neo4j** for knowledge graph storage
# - **Hugging Face all-MiniLM-L6-v2** for embeddings
# - **OpenAI GPT-4o-mini** for LLM (graph construction and QA)
# - **Wikipedia data** about the Roman Empire
# 
# ## Architecture
# ```
# User Question --> [Entity Extraction] --> [Graph Search (Fulltext)]
#               --> [Vector Search (Embeddings)]
#               --> [Combined Context] --> [LLM] --> Response
# ```

# ## 1. Setup & Configuration

# In[1]:


import os
import time
from typing import List

# Neo4j Configuration
NEO4J_URI = "bolt://localhost:7687"
NEO4J_USERNAME = "neo4j"
NEO4J_PASSWORD = ""
NEO4J_DATABASE = "policydblatest"

# Hugging Face Token (for embeddings)
HF_TOKEN = ""

# OpenAI API Key (for LLM)
OPENAI_API_KEY = ""

# Embedding Model
EMBEDDING_MODEL = "all-MiniLM-L6-v2"

print("Configuration loaded!")
print(f"Neo4j URI: {NEO4J_URI}")
print(f"Database: {NEO4J_DATABASE}")
print(f"Embedding Model: {EMBEDDING_MODEL}")


# ## 2. Initialize Hugging Face Embeddings

# In[88]:


from langchain_huggingface import HuggingFaceEmbeddings

print("Initializing Hugging Face Embeddings...")

embeddings = HuggingFaceEmbeddings(
    model_name=EMBEDDING_MODEL,
    model_kwargs={'device': 'cpu'},  # Use 'cuda' if GPU available
    encode_kwargs={'normalize_embeddings': True}
)

# Test embeddings
test_text = "this is an apple."
test_embedding = embeddings.embed_query(test_text)
print(f"[OK] Embeddings initialized!")
print(f"  Model: {EMBEDDING_MODEL}")
print(f"  Dimension: {len(test_embedding)}")


# ## 3. Initialize OpenAI LLM

# In[6]:


from langchain_openai import ChatOpenAI

print("Initializing OpenAI LLM...")

llm = ChatOpenAI(
    api_key=OPENAI_API_KEY,
    temperature=0,
    model="gpt-4o-mini"
)

# Test LLM
print("Testing LLM...")
test_response = llm.invoke("What is 2+2? Answer in one word.")
print(f"[OK] OpenAI LLM initialized (gpt-4o-mini)!")
print(f"  Test response: {test_response.content}")


# ## 4. Connect to Neo4j

# In[8]:


from langchain_neo4j import Neo4jGraph

print(f"Connecting to Neo4j database '{NEO4J_DATABASE}'...")

kg = Neo4jGraph(
    url=NEO4J_URI,
    username=NEO4J_USERNAME,
    password=NEO4J_PASSWORD,
    database=NEO4J_DATABASE
)

kg.refresh_schema()
print(f"[OK] Connected to Neo4j!")

# Check existing labels
labels = kg.query("CALL db.labels() YIELD label RETURN label")
print(f"Existing labels: {[l['label'] for l in labels]}")


# ## 5. Load Wikipedia Data (Roman Empire)

# In[10]:


from langchain_community.document_loaders import WikipediaLoader
from langchain_text_splitters import TokenTextSplitter

print("Loading Wikipedia data about Roman Empire...")

# Load Wikipedia articles
raw_documents = WikipediaLoader(query="The Roman empire").load()
print(f"  Loaded {len(raw_documents)} Wikipedia articles")

# Split into chunks
text_splitter = TokenTextSplitter(chunk_size=512, chunk_overlap=24)
documents = text_splitter.split_documents(raw_documents[:3])  # Use first 3 articles

print(f"[OK] Split into {len(documents)} chunks")
print(f"\nSample chunk:")
print(documents[0].page_content[:500])


# ## 6. Build Knowledge Graph with LLM Transformer
# 
# **Note**: This step uses the LLM to extract entities and relationships. Set `REBUILD_GRAPH = True` to rebuild.

# In[11]:


from langchain_experimental.graph_transformers import LLMGraphTransformer

# Set to True to rebuild the knowledge graph
REBUILD_GRAPH = True  # Change to True to rebuild

if REBUILD_GRAPH:
    print("Building Knowledge Graph with LLM Transformer...")
    print("This may take several minutes...")
    
    llm_transformer = LLMGraphTransformer(llm=llm)
    
    print("  Converting documents to graph format...")
    graph_documents = llm_transformer.convert_to_graph_documents(documents)
    print(f"  Created {len(graph_documents)} graph documents")
    
    print("  Adding to Neo4j...")
    kg.add_graph_documents(
        graph_documents,
        include_source=True,
        baseEntityLabel=True,  # Creates __Entity__ label
    )
    print("[OK] Knowledge Graph built!")
else:
    print("Skipping graph rebuild. Set REBUILD_GRAPH=True to rebuild.")


# ## 7. Check Database Contents

# In[14]:


print("Checking database contents...")

labels = kg.query("CALL db.labels() YIELD label RETURN label")
print(f"\nNode Labels: {[l['label'] for l in labels]}")

print("\nNode counts:")
for label_row in labels:
    label = label_row['label']
    count = kg.query(f"MATCH (n:`{label}`) RETURN count(n) as count")[0]['count']
    print(f"  {label}: {count} nodes")

# Sample entities
print("\nSample __Entity__ nodes:")
entities = kg.query("MATCH (e:__Entity__) RETURN e.id LIMIT 10")
for e in entities:
    print(f"  - {e['e.id']}")


# ## 8. Create Vector Index with Hugging Face Embeddings

# In[17]:


from langchain_neo4j import Neo4jVector

print("Creating Vector Index with Hugging Face Embeddings...")

try:
    vector_index = Neo4jVector.from_existing_graph(
        embedding=embeddings,
        url=NEO4J_URI,
        username=NEO4J_USERNAME,
        password=NEO4J_PASSWORD,
        database=NEO4J_DATABASE,
        search_type="hybrid",
        node_label="Document",
        text_node_properties=["text"],
        embedding_node_property="embedding",
    )
    print("[OK] Vector index created!")
except Exception as e:
    print(f"Could not create vector index from existing graph: {e}")
    print("Creating new vector index...")
    
    vector_index = Neo4jVector(
        embedding=embeddings,
        url=NEO4J_URI,
        username=NEO4J_USERNAME,
        password=NEO4J_PASSWORD,
        database=NEO4J_DATABASE,
        index_name="document_embeddings",
        node_label="Document",
        text_node_property="text",
        embedding_node_property="embedding",
    )
    print("[OK] New vector index created!")


# ## 9. Create Fulltext Index for Entity Search

# In[20]:


print("Creating Fulltext Index for Entity Search...")

# Check if __Entity__ nodes exist
entity_count = kg.query("MATCH (e:__Entity__) RETURN count(e) as count")[0]['count']
print(f"Found {entity_count} __Entity__ nodes")

if entity_count > 0:
    # Drop existing index
    try:
        kg.query("DROP INDEX entity IF EXISTS")
        print("  Dropped existing index")
    except:
        pass
    
    # Create fulltext index
    kg.query("CREATE FULLTEXT INDEX entity IF NOT EXISTS FOR (e:__Entity__) ON EACH [e.id]")
    print("  Fulltext index creation initiated")
    
    # Wait for index
    print("  Waiting for index to come online...")
    for i in range(30):
        result = kg.query("SHOW FULLTEXT INDEXES WHERE name = 'entity'")
        if result and result[0].get('state') == 'ONLINE':
            print(f"[OK] Index is ONLINE after {i+1} seconds!")
            break
        time.sleep(1)
    else:
        print("Index may still be populating")
else:
    print("No __Entity__ nodes found. Build the knowledge graph first (Step 6).")


# In[25]:


# Check index status
result = kg.query("SHOW FULLTEXT INDEXES WHERE name = 'entity'")
print(result)


# In[31]:


result = kg.query("SHOW INDEXES")
for idx in result:
    print(f"Name: {idx.get('name')}, Type: {idx.get('type')}, State: {idx.get('state')}")


# In[29]:


result = kg.query("MATCH (e:__Entity__) RETURN e.id LIMIT 5")
print(result)


# In[35]:


# Create the fulltext index
kg.query("CREATE FULLTEXT INDEX entity IF NOT EXISTS FOR (e:__Entity__) ON EACH [e.id]")

# Wait a moment and verify
import time
time.sleep(30)

result = kg.query("SHOW FULLTEXT INDEXES WHERE name = 'entity'")
print(result)


# ## 10. Setup Entity Extraction

# In[56]:


def extract_entities_simple(question: str) -> List[str]:
    """Extract person and organization names from text using LLM."""
    try:
        response = llm.invoke(
            f"Extract all person and organization names from this text. "
            f"Return ONLY the names as a comma-separated list, nothing else.\n\n"
            f"Text: {question}"
        )
        entities = [e.strip() for e in response.content.split(',') if e.strip()]
        return entities[:5]
    except Exception as e:
        print(f"  Entity extraction error: {e}")
        return []

# Test
print("Testing entity extraction...")
test_entities = extract_entities_simple("Who was Aurelian and what did he do for the Roman Empire?")
print(f"[OK] Extracted entities: {test_entities}")


# In[37]:


result = kg.query("CALL db.info()")
print(result)


# In[39]:


# Drop if exists first
try:
    kg.query("DROP INDEX entity IF EXISTS")
    print("Dropped existing")
except Exception as e:
    print(f"Drop error: {e}")

# Create index
kg.query("""
CREATE FULLTEXT INDEX entity 
FOR (n:__Entity__) 
ON EACH [n.id]
""")
print("Created!")


# In[41]:


result = kg.query("SHOW FULLTEXT INDEXES")
print(result)


# In[90]:


def extract_entities_simple(question: str) -> List[str]:
    """Extract person and organization names from text using LLM."""
    try:
        response = llm.invoke(
            f"Extract all person and organization names from this text. "
            f"Return ONLY the names as a comma-separated list, nothing else.\n\n"
            f"Text: {question}"
        )
        entities = [e.strip() for e in response.content.split(',') if e.strip()]
        return entities[:5]
    except Exception as e:
        print(f"  Entity extraction error: {e}")
        return []

# Test
print("Testing entity extraction...")
test_entities = extract_entities_simple("Who was Aurelian and what did he do for the Roman Empire?")
print(f"[OK] Extracted entities: {test_entities}")


# ## 11. Setup Structured Retriever (Graph Search)

# In[43]:


from langchain_neo4j.vectorstores.neo4j_vector import remove_lucene_chars

def generate_full_text_query(input: str) -> str:
    """Generate a full-text search query with fuzzy matching."""
    full_text_query = ""
    words = [el for el in remove_lucene_chars(input).split() if el]
    if not words:
        return ""
    for word in words[:-1]:
        full_text_query += f" {word}~2 AND"
    full_text_query += f" {words[-1]}~2"
    return full_text_query.strip()


def structured_retriever(question: str) -> str:
    """Retrieve graph context via entity search and relationship traversal."""
    result = ""
    entities = extract_entities_simple(question)
    
    if not entities:
        print("  No entities extracted")
        return result
    
    for entity in entities:
        print(f"  Searching for entity: {entity}")
        query = generate_full_text_query(entity)
        if not query:
            continue
            
        try:
            response = kg.query(
                """CALL db.index.fulltext.queryNodes('entity', $query, {limit:2})
                YIELD node, score
                CALL (node) {
                    MATCH (node)-[r:!MENTIONS]->(neighbor)
                    RETURN node.id + ' - ' + type(r) + ' -> ' + neighbor.id AS output
                    UNION ALL
                    MATCH (node)<-[r:!MENTIONS]-(neighbor)
                    RETURN neighbor.id + ' - ' + type(r) + ' -> ' + node.id AS output
                }
                RETURN output LIMIT 50
                """,
                {"query": query},
            )
            result += "\n".join([el["output"] for el in response if el.get("output")])
            print(f"    Found {len(response)} relationships")
        except Exception as e:
            print(f"  Graph search error: {e}")
    
    return result

print("[OK] Structured retriever ready!")


# ## 12. Setup Combined Retriever (Graph + Vector)

# In[46]:


def retriever(question: str) -> str:
    """Hybrid retriever combining graph traversal and vector similarity."""
    print(f"\n[Retrieval] Query: '{question}'")
    print("-" * 50)
    
    # Graph search
    print("\n[Graph Search]")
    structured_data = structured_retriever(question)
    
    # Vector search
    print("\n[Vector Search]")
    try:
        unstructured_results = vector_index.similarity_search(question, k=3)
        unstructured_data = [doc.page_content for doc in unstructured_results]
        print(f"  Found {len(unstructured_data)} similar documents")
    except Exception as e:
        print(f"  Vector search error: {e}")
        unstructured_data = []
    
    # Combine
    final_data = f"""=== Structured Graph Data ===
{structured_data if structured_data else "No structured data found"}

=== Unstructured Vector Data ===
{"#Document ".join(unstructured_data) if unstructured_data else "No unstructured data found"}
"""
    
    print("-" * 50)
    return final_data

print("[OK] Combined retriever ready!")


# ## 13. Build RAG Chain

# In[49]:


from langchain_core.prompts import ChatPromptTemplate
from langchain_core.output_parsers import StrOutputParser
from langchain_core.runnables import RunnablePassthrough, RunnableParallel

rag_template = """Answer the question based only on the following context:

{context}

Question: {question}

Instructions:
- Use natural language and be concise
- If the context doesn't contain relevant information, say so
- Cite specific facts from the context when possible

Answer:"""

rag_prompt = ChatPromptTemplate.from_template(rag_template)

rag_chain = (
    RunnableParallel(
        {
            "context": retriever,
            "question": RunnablePassthrough(),
        }
    )
    | rag_prompt
    | llm
    | StrOutputParser()
)

print("[OK] RAG chain built!")


# ## 14. Test the Graph RAG Pipeline!

# In[52]:


def ask_question(question: str):
    """Run a question through the RAG pipeline."""
    print("\n" + "=" * 60)
    print(f"QUESTION: {question}")
    print("=" * 60)
    
    try:
        response = rag_chain.invoke(question)
        print("\n" + "=" * 60)
        print("ANSWER:")
        print("=" * 60)
        print(response)
    except Exception as e:
        print(f"\nError: {e}")
    
    print("\n" + "=" * 60)


# In[58]:


# Test Question 1
ask_question("Who was Aurelian?")


# In[60]:


# Test Question 2
ask_question("How did the Western Roman Empire finally collapse?")


# In[62]:


# Test Question 3
ask_question("What was the Pax Romana?")


# In[64]:


# Ask your own question!
your_question = "Who was the first Roman emperor?"
ask_question(your_question)


# ## Summary
# 
# This notebook demonstrated a complete **Graph RAG** pipeline:
# 
# 1. **Hugging Face Embeddings** (`all-MiniLM-L6-v2`) for vector similarity search
# 2. **OpenAI LLM** (`gpt-4o-mini`) for entity extraction and answer generation
# 3. **Neo4j Knowledge Graph** for structured data storage and traversal
# 4. **Hybrid Retrieval** combining graph search and vector search
# 
# ### Key Components:
# - `__Entity__` nodes contain extracted entities with relationships
# - `Document` nodes contain text chunks with embeddings
# - Fulltext index enables fuzzy entity matching
# - Vector index enables semantic similarity search

# In[66]:


def extract_entities_simple(question: str) -> List[str]:
    """Extract person and organization names from text using LLM."""
    try:
        response = llm.invoke(
            f"Extract all person and organization names from this text. "
            f"Return ONLY the names as a comma-separated list, nothing else.\n\n"
            f"Text: {question}"
        )
        entities = [e.strip() for e in response.content.split(',') if e.strip()]
        print(f"  >> Extracted entities: {entities}")
        return entities[:5]
    except Exception as e:
        print(f"  Entity extraction error: {e}")
        return []


# In[68]:


from langchain_neo4j.vectorstores.neo4j_vector import remove_lucene_chars

def generate_full_text_query(input: str) -> str:
    full_text_query = ""
    words = [el for el in remove_lucene_chars(input).split() if el]
    if not words:
        return ""
    for word in words[:-1]:
        full_text_query += f" {word}~2 AND"
    full_text_query += f" {words[-1]}~2"
    return full_text_query.strip()

def structured_retriever(question: str) -> str:
    """Retrieve graph context with detailed output."""
    result = ""
    entities = extract_entities_simple(question)
    
    if not entities:
        print("  >> No entities found in question")
        return result
    
    for entity in entities:
        query = generate_full_text_query(entity)
        print(f"\n  >> Searching graph for: '{entity}'")
        print(f"     Fulltext query: '{query}'")
        
        if not query:
            continue
            
        try:
            # First find matching nodes
            nodes = kg.query(
                """CALL db.index.fulltext.queryNodes('entity', $query, {limit:3})
                YIELD node, score
                RETURN node.id AS entity, score""",
                {"query": query},
            )
            
            if nodes:
                print(f"     Found {len(nodes)} matching entities:")
                for n in nodes:
                    print(f"       - {n['entity']} (score: {n['score']:.3f})")
            else:
                print(f"     No matching entities found")
                continue
            
            # Now get relationships
            response = kg.query(
                """CALL db.index.fulltext.queryNodes('entity', $query, {limit:2})
                YIELD node, score
                CALL (node) {
                    MATCH (node)-[r:!MENTIONS]->(neighbor)
                    RETURN node.id + ' - ' + type(r) + ' -> ' + neighbor.id AS output
                    UNION ALL
                    MATCH (node)<-[r:!MENTIONS]-(neighbor)
                    RETURN neighbor.id + ' - ' + type(r) + ' -> ' + node.id AS output
                }
                RETURN output LIMIT 20
                """,
                {"query": query},
            )
            
            if response:
                print(f"     Found {len(response)} relationships:")
                for rel in response[:10]:  # Show first 10
                    if rel.get("output"):
                        print(f"       {rel['output']}")
                        result += rel["output"] + "\n"
            else:
                print(f"     No relationships found")
                
        except Exception as e:
            print(f"     Graph search error: {e}")
    
    return result

print("[OK] Enhanced structured retriever ready!")


# In[70]:


def retriever(question: str) -> str:
    """Hybrid retriever with detailed output."""
    print("\n" + "=" * 70)
    print(f"RETRIEVAL FOR: '{question}'")
    print("=" * 70)
    
    # Graph search
    print("\n[1] GRAPH SEARCH (Knowledge Graph)")
    print("-" * 50)
    structured_data = structured_retriever(question)
    
    # Vector search
    print("\n[2] VECTOR SEARCH (Semantic Similarity)")
    print("-" * 50)
    try:
        unstructured_results = vector_index.similarity_search(question, k=3)
        unstructured_data = []
        print(f"  >> Found {len(unstructured_results)} similar documents:")
        for i, doc in enumerate(unstructured_results):
            preview = doc.page_content[:150].replace('\n', ' ')
            print(f"\n  Document {i+1}:")
            print(f"    '{preview}...'")
            unstructured_data.append(doc.page_content)
    except Exception as e:
        print(f"  >> Vector search error: {e}")
        unstructured_data = []
    
    # Combine
    final_data = f"""=== Structured Graph Data ===
{structured_data if structured_data else "No structured data found"}

=== Unstructured Vector Data ===
{"#Document ".join(unstructured_data) if unstructured_data else "No unstructured data found"}
"""
    
    print("\n" + "=" * 70)
    print("CONTEXT ASSEMBLED - Sending to LLM...")
    print("=" * 70)
    
    return final_data

print("[OK] Enhanced retriever ready!")


# In[72]:


def ask_question(question: str):
    """Run a question with full visibility."""
    print("\n" + "#" * 70)
    print(f"# QUESTION: {question}")
    print("#" * 70)
    
    try:
        response = rag_chain.invoke(question)
        print("\n" + "#" * 70)
        print("# FINAL ANSWER:")
        print("#" * 70)
        print(f"\n{response}\n")
    except Exception as e:
        print(f"\nError: {e}")

print("[OK] Enhanced ask_question ready!")


# In[74]:


ask_question("Who was Aurelian?")


# In[76]:


# Test Question 2
ask_question("How did the Western Roman Empire finally collapse?")


# In[80]:


from langchain_neo4j import GraphCypherQAChain
from langchain_core.prompts import PromptTemplate

print("Setting up Text2Cypher (Natural Language to Cypher)...")

# Refresh schema for better query generation
kg.refresh_schema()

# Custom prompt with examples (improves accuracy)
CYPHER_GENERATION_TEMPLATE = """Task: Generate Cypher statement to query a graph database.

Instructions:
Use only the provided relationship types and properties in the schema.
Do not use any other relationship types or properties that are not provided.

Schema:
{schema}

Note: Do not include any explanations or apologies in your responses.
Do not respond to any questions that might ask anything else than for you to construct a Cypher statement.
Do not include any text except the generated Cypher statement.

Examples:
Question: Who was Aurelian?
Cypher: MATCH (e:__Entity__ {{id: "Aurelian"}})-[r]-(related) RETURN e, type(r), related LIMIT 10

Question: What did the Roman Empire control?
Cypher: MATCH (e:__Entity__ {{id: "Roman Empire"}})-[r]->(related) RETURN type(r), related.id LIMIT 20

Question: Show me all entities related to Rome
Cypher: MATCH (e:__Entity__) WHERE e.id CONTAINS "Rome" MATCH (e)-[r]-(related) RETURN e.id, type(r), related.id LIMIT 15

The question is:
{question}"""

CYPHER_GENERATION_PROMPT = PromptTemplate(
    input_variables=["schema", "question"], 
    template=CYPHER_GENERATION_TEMPLATE
)

# Create the chain with security acknowledgment
cypher_chain = GraphCypherQAChain.from_llm(
    llm,
    graph=kg,
    verbose=True,
    cypher_prompt=CYPHER_GENERATION_PROMPT,
    return_intermediate_steps=True,
    validate_cypher=True,
    top_k=10,
    allow_dangerous_requests=True  # ⚠️ ADD THIS LINE
)

print("[OK] Text2Cypher chain ready!")


# In[82]:


def ask_cypher(question: str):
    """Ask a question and see the generated Cypher query."""
    print("\n" + "=" * 70)
    print(f"QUESTION: {question}")
    print("=" * 70)
    
    try:
        result = cypher_chain.invoke({"query": question})
        
        # Show generated Cypher
        if 'intermediate_steps' in result:
            print("\n[GENERATED CYPHER QUERY]:")
            print("-" * 70)
            cypher_query = result['intermediate_steps'][0]['query']
            print(cypher_query)
            
            # Show database results
            print("\n[DATABASE RESULTS]:")
            print("-" * 70)
            db_results = result['intermediate_steps'][1]['context']
            for i, res in enumerate(db_results[:5], 1):
                print(f"{i}. {res}")
        
        # Show final answer
        print("\n[FINAL ANSWER]:")
        print("=" * 70)
        print(result['result'])
        print("=" * 70)
        
    except Exception as e:
        print(f"\nError: {e}")

print("[OK] Interactive Text2Cypher ready!")


# In[84]:


ask_cypher("What territories did the Roman Empire control?")


# In[86]:


def compare_retrieval(question: str):
    """Compare Fulltext+Vector vs Text2Cypher approaches."""
    print("\n" + "#" * 70)
    print(f"# COMPARING APPROACHES FOR: {question}")
    print("#" * 70)
    
    # Approach 1: Fulltext + Vector (your current setup)
    print("\n[APPROACH 1: Fulltext Index + Vector Search]")
    print("-" * 70)
    hybrid_result = rag_chain.invoke(question)
    print(f"Answer: {hybrid_result}\n")
    
    # Approach 2: Text2Cypher
    print("\n[APPROACH 2: Text2Cypher (Natural Language → Cypher)]")
    print("-" * 70)
    cypher_result = cypher_chain.invoke({"query": question})
    print(f"Generated Cypher: {cypher_result['intermediate_steps'][0]['query']}")
    print(f"Answer: {cypher_result['result']}\n")

# Test comparison
compare_retrieval("Who was Aurelian?")


# - Aurelian was a Roman emperor who reigned from 270 to 275 AD. He is noted for reunifying the Roman Empire during a time of crisis, which included civil wars, plagues, and barbarian invasions. His efforts helped restore stability to the empire after it had been fragmented into separate regions, such as the Gallic and Palmyrene empires.

# In[ ]:




