"""
LangGraph Workflow for Agentic Fraud Detection
===============================================
Main workflow that orchestrates pattern processing with human-in-the-loop.
"""

from typing import Dict, List, Optional, Literal, Any
from langgraph.graph import StateGraph, END
from langchain_core.messages import HumanMessage, AIMessage, SystemMessage

from state import AgentState, create_initial_state
from genie_tool import GenieTool
from sql_storage import SQLStorage
from sql_executor import SQLExecutor
from config import Config


def create_llm(config: Config):
    """Create LLM based on configuration."""
    if config.llm_provider == "anthropic":
        from langchain_anthropic import ChatAnthropic
        return ChatAnthropic(
            model=config.anthropic_model,
            temperature=0,
            api_key=config.anthropic_api_key
        )
    else:
        from langchain_openai import ChatOpenAI
        return ChatOpenAI(
            model=config.openai_model,
            temperature=0,
            api_key=config.openai_api_key
        )


class FraudDetectionWorkflow:
    """
    LangGraph-based workflow for fraud pattern detection.
    
    Workflow:
    1. Parse pattern into steps
    2. For each step:
       a. Generate SQL using Genie
       b. Ask human for approval (yes/no/edit)
       c. Execute SQL
       d. Ask for feedback on results
       e. Store approved SQL
    3. Combine all steps into final function
    4. Execute final function
    5. Get final approval
    6. Insert tool into database
    """
    
    def __init__(self, config: Config, genie: GenieTool, 
                 sql_executor: SQLExecutor, sql_storage: SQLStorage):
        """
        Initialize workflow.
        
        Args:
            config: Configuration object
            genie: Genie tool for SQL generation
            sql_executor: SQL executor for running queries
            sql_storage: SQL storage for persisting queries
        """
        self.config = config
        self.genie = genie
        self.sql_executor = sql_executor
        self.sql_storage = sql_storage
        
        # Initialize LLM for orchestration (Anthropic or OpenAI)
        self.llm = create_llm(config)
        print(f"[OK] LLM initialized: {config.llm_provider} ({config.anthropic_model if config.llm_provider == 'anthropic' else config.openai_model})")
        
        # Build the graph
        self.graph = self._build_graph()
    
    def _build_graph(self) -> StateGraph:
        """Build the LangGraph workflow."""
        
        # Create workflow graph
        workflow = StateGraph(AgentState)
        
        # Add nodes
        workflow.add_node("parse_pattern", self._parse_pattern)
        workflow.add_node("generate_sql", self._generate_sql)
        workflow.add_node("await_sql_approval", self._await_sql_approval)
        workflow.add_node("execute_step", self._execute_step)
        workflow.add_node("await_execution_feedback", self._await_execution_feedback)
        workflow.add_node("store_step_sql", self._store_step_sql)
        workflow.add_node("next_step", self._next_step)
        workflow.add_node("combine_to_function", self._combine_to_function)
        workflow.add_node("execute_final", self._execute_final)
        workflow.add_node("await_final_approval", self._await_final_approval)
        workflow.add_node("insert_tool", self._insert_tool)
        workflow.add_node("rethink", self._rethink)
        workflow.add_node("complete", self._complete)
        
        # Set entry point
        workflow.set_entry_point("parse_pattern")
        
        # Add edges
        workflow.add_edge("parse_pattern", "generate_sql")
        
        # From generate_sql, go to await approval
        workflow.add_edge("generate_sql", "await_sql_approval")
        
        # From await_sql_approval, conditional based on user response
        workflow.add_conditional_edges(
            "await_sql_approval",
            self._route_sql_approval,
            {
                "execute": "execute_step",
                "regenerate": "generate_sql",
                "edit": "await_sql_approval"  # Stay in same node for edit
            }
        )
        
        # From execute_step, go to await feedback
        workflow.add_edge("execute_step", "await_execution_feedback")
        
        # From await_execution_feedback, conditional
        workflow.add_conditional_edges(
            "await_execution_feedback",
            self._route_execution_feedback,
            {
                "store": "store_step_sql",
                "regenerate": "generate_sql"
            }
        )
        
        # From store_step_sql, go to next_step
        workflow.add_edge("store_step_sql", "next_step")
        
        # From next_step, conditional
        workflow.add_conditional_edges(
            "next_step",
            self._route_next_step,
            {
                "continue": "generate_sql",
                "combine": "combine_to_function"
            }
        )
        
        # From combine_to_function, execute final
        workflow.add_edge("combine_to_function", "execute_final")
        
        # From execute_final, await final approval
        workflow.add_edge("execute_final", "await_final_approval")
        
        # From await_final_approval, conditional
        workflow.add_conditional_edges(
            "await_final_approval",
            self._route_final_approval,
            {
                "insert": "insert_tool",
                "rethink": "rethink"
            }
        )
        
        # From rethink, go back to combine
        workflow.add_edge("rethink", "combine_to_function")
        
        # From insert_tool, complete
        workflow.add_edge("insert_tool", "complete")
        
        # Complete is end
        workflow.add_edge("complete", END)
        
        return workflow.compile()
    
    # =========================================================================
    # Node Functions
    # =========================================================================
    
    def _parse_pattern(self, state: AgentState) -> Dict:
        """Parse pattern and prepare steps."""
        print("\n" + "="*60)
        print(f"Processing Pattern: {state['pattern_name']}")
        print("="*60)
        print(f"\nPattern ID: {state['pattern_id']}")
        print(f"Description: {state['pattern_description'][:200]}...")
        print(f"\nDetection Steps: {state['total_steps']}")
        
        for i, step in enumerate(state['steps'], 1):
            print(f"  Step {i}: {step}")
        
        # Set first step
        return {
            "current_step_index": 0,
            "current_step_description": state['steps'][0] if state['steps'] else "",
            "status": "processing",
            "messages": [{
                "role": "system",
                "content": f"Starting pattern processing: {state['pattern_name']}"
            }]
        }
    
    def _generate_sql(self, state: AgentState) -> Dict:
        """Generate SQL for current step using Genie."""
        step_idx = state['current_step_index']
        step_desc = state['current_step_description']
        
        print(f"\n{'='*60}")
        print(f"STEP {step_idx + 1}/{state['total_steps']}: Generating SQL")
        print(f"{'='*60}")
        print(f"\nStep Description: {step_desc}")
        
        # Build prompt for Genie
        prompt = self._build_genie_prompt(state, step_desc)
        
        print(f"\nSending to Genie...")
        
        # Generate SQL using Genie
        sql_query, error = self.genie.generate_sql(prompt)
        
        if error:
            print(f"[ERROR] Genie error: {error}")
            # Generate fallback SQL using LLM
            sql_query = self._generate_fallback_sql(state, step_desc)
        
        print(f"\nGenerated SQL:")
        print(f"```sql\n{sql_query}\n```")
        
        return {
            "current_sql_query": sql_query,
            "current_sql_approved": False,
            "awaiting_feedback": True,
            "feedback_type": "sql_approval",
            "messages": [{
                "role": "assistant",
                "content": f"Generated SQL for step {step_idx + 1}: {sql_query[:200]}..."
            }]
        }
    
    def _await_sql_approval(self, state: AgentState) -> Dict:
        """Wait for human approval of SQL."""
        print(f"\n{'='*60}")
        print("AWAITING SQL APPROVAL")
        print(f"{'='*60}")
        print("\nGenerated SQL:")
        print(f"```sql\n{state['current_sql_query']}\n```")
        print("\nOptions:")
        print("  [yes/y] - Approve and execute")
        print("  [no/n]  - Reject and regenerate")
        print("  [edit]  - Edit the SQL manually")
        
        response = input("\nYour choice: ").strip().lower()
        
        if response in ['yes', 'y']:
            return {
                "current_sql_approved": True,
                "user_feedback": "approved",
                "awaiting_feedback": False
            }
        elif response == 'edit':
            print("\nEnter your edited SQL (end with an empty line):")
            lines = []
            while True:
                line = input()
                if line == "":
                    break
                lines.append(line)
            edited_sql = "\n".join(lines)
            
            return {
                "current_sql_query": edited_sql,
                "user_edit": edited_sql,
                "current_sql_approved": True,
                "user_feedback": "edited",
                "awaiting_feedback": False
            }
        else:
            return {
                "current_sql_approved": False,
                "user_feedback": "rejected",
                "awaiting_feedback": False
            }
    
    def _execute_step(self, state: AgentState) -> Dict:
        """Execute the current step's SQL."""
        print(f"\n{'='*60}")
        print("EXECUTING SQL")
        print(f"{'='*60}")
        
        sql_query = state['current_sql_query']
        
        results, error = self.sql_executor.execute_and_format(sql_query, limit=20)
        
        if error:
            print(f"\n[ERROR] Execution failed: {error}")
            return {
                "current_execution_result": None,
                "current_execution_error": error,
                "awaiting_feedback": True,
                "feedback_type": "execution_result"
            }
        
        print(f"\n[OK] Query executed successfully")
        print(f"Returned {len(results)} rows")
        
        if results:
            print("\nSample Results:")
            for i, row in enumerate(results[:5], 1):
                print(f"  Row {i}: {row}")
            if len(results) > 5:
                print(f"  ... and {len(results) - 5} more rows")
        
        return {
            "current_execution_result": results,
            "current_execution_error": None,
            "awaiting_feedback": True,
            "feedback_type": "execution_result"
        }
    
    def _await_execution_feedback(self, state: AgentState) -> Dict:
        """Wait for feedback on execution results."""
        print(f"\n{'='*60}")
        print("AWAITING EXECUTION FEEDBACK")
        print(f"{'='*60}")
        
        if state['current_execution_error']:
            print(f"\nExecution Error: {state['current_execution_error']}")
            print("\nDo you want to regenerate the SQL? [yes/no]")
        else:
            print(f"\nResults look correct? ({len(state['current_execution_result'] or [])} rows)")
            print("  [yes/y] - Results are correct, continue")
            print("  [no/n]  - Results are wrong, regenerate SQL")
        
        response = input("\nYour choice: ").strip().lower()
        
        if response in ['yes', 'y']:
            return {
                "user_feedback": "approved",
                "awaiting_feedback": False
            }
        else:
            return {
                "user_feedback": "rejected",
                "awaiting_feedback": False
            }
    
    def _store_step_sql(self, state: AgentState) -> Dict:
        """Store the approved SQL for this step."""
        step_idx = state['current_step_index']
        step_id = f"step_{step_idx + 1}"
        
        print(f"\n[OK] Storing SQL for Step {step_idx + 1}")
        
        # Store in SQL storage
        self.sql_storage.add_step_query(
            step_id=step_id,
            step_description=state['current_step_description'],
            sql_query=state['current_sql_query'],
            approved=True,
            edited=state['user_edit'] is not None
        )
        
        # Add to state
        step_data = {
            "step_id": step_id,
            "step_index": step_idx,
            "description": state['current_step_description'],
            "sql_query": state['current_sql_query'],
            "edited": state['user_edit'] is not None,
            "row_count": len(state['current_execution_result'] or [])
        }
        
        return {
            "step_sql_queries": [step_data],  # This will be accumulated
            "user_edit": None  # Reset for next step
        }
    
    def _next_step(self, state: AgentState) -> Dict:
        """Move to next step or combine."""
        next_idx = state['current_step_index'] + 1
        
        if next_idx >= state['total_steps']:
            print(f"\n[OK] All {state['total_steps']} steps completed!")
            return {
                "current_step_index": next_idx
            }
        
        print(f"\n[OK] Moving to Step {next_idx + 1}/{state['total_steps']}")
        
        return {
            "current_step_index": next_idx,
            "current_step_description": state['steps'][next_idx],
            "current_sql_query": "",
            "current_sql_approved": False,
            "current_execution_result": None,
            "current_execution_error": None
        }
    
    def _combine_to_function(self, state: AgentState) -> Dict:
        """Combine all step SQLs into a final function."""
        print(f"\n{'='*60}")
        print("COMBINING INTO FINAL FUNCTION")
        print(f"{'='*60}")
        
        # Get all step queries
        step_queries = self.sql_storage.get_all_queries()
        
        # Generate combined SQL using LLM
        combined_sql = self._generate_combined_function(state, step_queries)
        
        # Generate function name
        function_name = f"detect_{state['pattern_id'].lower().replace('-', '_')}"
        
        print(f"\nFunction Name: {function_name}")
        print(f"\nCombined SQL:")
        print(f"```sql\n{combined_sql}\n```")
        
        # Store in SQL storage
        self.sql_storage.set_final_function(combined_sql, function_name)
        
        return {
            "final_sql_function": combined_sql,
            "final_function_name": function_name
        }
    
    def _execute_final(self, state: AgentState) -> Dict:
        """Execute the final combined function."""
        print(f"\n{'='*60}")
        print("EXECUTING FINAL FUNCTION")
        print(f"{'='*60}")
        
        results, error = self.sql_executor.execute_and_format(
            state['final_sql_function'], 
            limit=50
        )
        
        if error:
            print(f"\n[ERROR] Final execution failed: {error}")
            return {
                "final_result": None,
                "final_error": error,
                "awaiting_feedback": True,
                "feedback_type": "final_approval"
            }
        
        print(f"\n[OK] Final function executed successfully")
        print(f"Total fraudulent claims detected: {len(results)}")
        
        if results:
            print("\nResults:")
            for i, row in enumerate(results[:10], 1):
                print(f"  {i}. {row}")
            if len(results) > 10:
                print(f"  ... and {len(results) - 10} more rows")
        
        return {
            "final_result": results,
            "final_error": None,
            "awaiting_feedback": True,
            "feedback_type": "final_approval"
        }
    
    def _await_final_approval(self, state: AgentState) -> Dict:
        """Wait for final approval."""
        print(f"\n{'='*60}")
        print("AWAITING FINAL APPROVAL")
        print(f"{'='*60}")
        
        if state['final_error']:
            print(f"\nError: {state['final_error']}")
        else:
            print(f"\nTotal results: {len(state['final_result'] or [])} fraudulent claims")
        
        print("\nAre these results correct?")
        print("  [yes/y] - Approve and save as tool")
        print("  [no/n]  - Reject and rethink")
        
        response = input("\nYour choice: ").strip().lower()
        
        if response in ['yes', 'y']:
            return {
                "final_approved": True,
                "user_feedback": "approved",
                "awaiting_feedback": False
            }
        else:
            return {
                "final_approved": False,
                "user_feedback": "rejected",
                "awaiting_feedback": False
            }
    
    def _rethink(self, state: AgentState) -> Dict:
        """Rethink and regenerate the final function."""
        print(f"\n{'='*60}")
        print("RETHINKING...")
        print(f"{'='*60}")
        
        print("\nWhat would you like to change?")
        feedback = input("Your feedback: ").strip()
        
        # Use LLM to regenerate based on feedback
        # For now, we'll just return to combine with the feedback stored
        
        return {
            "user_feedback": feedback,
            "final_approved": False
        }
    
    def _insert_tool(self, state: AgentState) -> Dict:
        """Insert the function as a tool in the database."""
        print(f"\n{'='*60}")
        print("INSERTING TOOL INTO DATABASE")
        print(f"{'='*60}")
        
        tool_id = f"tool_{state['pattern_id']}"
        policy_id = "UHC-POL-2026-0005A"  # Get from pattern or config
        
        # Insert tool
        success, error = self.sql_executor.insert_tool(
            tool_id=tool_id,
            pattern_id=state['pattern_id'],
            policy_id=policy_id,
            sql_query=state['final_sql_function'],
            tools_table=self.config.tools_table
        )
        
        if error:
            print(f"\n[ERROR] Failed to insert tool: {error}")
            return {
                "tool_id": tool_id,
                "tool_inserted": False,
                "error": error
            }
        
        # Update pattern with tool_id
        success, error = self.sql_executor.update_pattern_tool(
            pattern_id=state['pattern_id'],
            tool_id=tool_id,
            patterns_table=self.config.patterns_table
        )
        
        if error:
            print(f"\n[WARNING] Failed to update pattern: {error}")
        
        print(f"\n[OK] Tool inserted successfully: {tool_id}")
        
        return {
            "tool_id": tool_id,
            "tool_inserted": True
        }
    
    def _complete(self, state: AgentState) -> Dict:
        """Complete the workflow."""
        print(f"\n{'='*60}")
        print("WORKFLOW COMPLETE!")
        print(f"{'='*60}")
        
        print(f"\nPattern: {state['pattern_name']}")
        print(f"Pattern ID: {state['pattern_id']}")
        print(f"Tool ID: {state['tool_id']}")
        print(f"Tool Inserted: {state['tool_inserted']}")
        print(f"Total Steps: {state['total_steps']}")
        print(f"Fraudulent Claims Found: {len(state['final_result'] or [])}")
        
        print(f"\nSQL code saved to: {self.sql_storage.filepath}")
        
        return {
            "status": "completed"
        }
    
    # =========================================================================
    # Routing Functions
    # =========================================================================
    
    def _route_sql_approval(self, state: AgentState) -> str:
        """Route based on SQL approval."""
        if state['current_sql_approved']:
            return "execute"
        elif state['user_feedback'] == "edited":
            return "execute"
        else:
            return "regenerate"
    
    def _route_execution_feedback(self, state: AgentState) -> str:
        """Route based on execution feedback."""
        if state['user_feedback'] == "approved":
            return "store"
        else:
            return "regenerate"
    
    def _route_next_step(self, state: AgentState) -> str:
        """Route based on step progress."""
        if state['current_step_index'] >= state['total_steps']:
            return "combine"
        else:
            return "continue"
    
    def _route_final_approval(self, state: AgentState) -> str:
        """Route based on final approval."""
        if state['final_approved']:
            return "insert"
        else:
            return "rethink"
    
    # =========================================================================
    # Helper Functions
    # =========================================================================
    
    def _build_genie_prompt(self, state: AgentState, step_desc: str) -> str:
        """Build prompt for Genie."""
        # Include context from previous steps
        context = ""
        if state['step_sql_queries']:
            context = "\n\nPrevious steps completed:\n"
            for sq in state['step_sql_queries']:
                context += f"- Step {sq['step_index'] + 1}: {sq['description']}\n"
                context += f"  SQL: {sq['sql_query'][:100]}...\n"
        
        # Table schema for accurate SQL generation
        table_schema = """
Table: fraud_detection.test_data.claims
Columns:
  - claim_id STRING (primary key)
  - patient_id STRING
  - provider_npi STRING
  - provider_tin STRING
  - provider_specialty STRING
  - service_date DATE
  - procedure_code STRING (surgical procedure codes like 27447, 29881)
  - global_days_value STRING (values: '010', '090', '000', 'XXX')
  - em_code STRING (E/M codes like 99213, 99214 - NULL if not E/M)
  - modifier_24 STRING (NULL if missing)
  - modifier_58 STRING (NULL if missing)
  - fare_amount DOUBLE
  - claim_status STRING
  - created_at TIMESTAMP
"""
        
        prompt = f"""Generate Spark SQL for this fraud detection step:

Pattern: {state['pattern_name']}
Overall Goal: {state['pattern_description']}

{table_schema}

Current Step (Step {state['current_step_index'] + 1} of {state['total_steps']}):
{step_desc}
{context}
Requirements:
1. Use table: {self.config.claims_table}
2. Use EXACT column names from the schema above (e.g., global_days_value NOT global_days)
3. Return ONLY SQL (no markdown, no explanations)
4. Use proper Spark SQL syntax
5. Include LIMIT 50
6. Build upon previous steps if applicable

Generate the SQL query:"""
        
        return prompt
    
    def _generate_fallback_sql(self, state: AgentState, step_desc: str) -> str:
        """Generate fallback SQL using LLM when Genie fails."""
        messages = [
            SystemMessage(content="You are a SQL expert. Generate ONLY SQL code, no explanations."),
            HumanMessage(content=self._build_genie_prompt(state, step_desc))
        ]
        
        response = self.llm.invoke(messages)
        sql = response.content.strip()
        
        # Clean up SQL (remove markdown if present)
        if sql.startswith("```"):
            sql = sql.split("```")[1]
            if sql.startswith("sql"):
                sql = sql[3:]
        sql = sql.strip()
        
        return sql
    
    def _generate_combined_function(self, state: AgentState, step_queries: List[Dict]) -> str:
        """Generate combined SQL function from all steps."""
        
        # Build prompt for LLM
        steps_sql = "\n\n".join([
            f"-- Step {i+1}: {sq['step_description']}\n{sq['sql_query']}"
            for i, sq in enumerate(step_queries)
        ])
        
        prompt = f"""Combine these SQL steps into a single, optimized SQL query for fraud detection:

Pattern: {state['pattern_name']}
Goal: {state['pattern_description']}

Individual Steps:
{steps_sql}

Requirements:
1. Combine into a single SELECT query
2. Use CTEs (WITH clauses) if needed for clarity
3. Return the final fraudulent claims with all relevant columns
4. Include LIMIT 50
5. Use table: {self.config.claims_table}
6. Optimize for performance
7. Return ONLY the SQL, no explanations

Generate the combined SQL:"""
        
        messages = [
            SystemMessage(content="You are a SQL expert. Generate ONLY SQL code, no markdown."),
            HumanMessage(content=prompt)
        ]
        
        response = self.llm.invoke(messages)
        sql = response.content.strip()
        
        # Clean up SQL
        if sql.startswith("```"):
            sql = sql.split("```")[1]
            if sql.startswith("sql"):
                sql = sql[3:]
        sql = sql.strip()
        
        return sql
    
    # =========================================================================
    # Public Methods
    # =========================================================================
    
    def run(self, pattern: Dict) -> AgentState:
        """
        Run the workflow for a pattern.
        
        Args:
            pattern: Pattern dictionary from patterns.json
            
        Returns:
            Final agent state
        """
        # Create initial state
        initial_state = create_initial_state(pattern)
        
        # Clear previous SQL storage
        self.sql_storage.clear()
        
        # Run the graph with increased recursion limit
        final_state = self.graph.invoke(
            initial_state,
            config={"recursion_limit": 100}
        )
        
        return final_state

