"""
main.py - Foodly AI Support Agent Entry Point

This is the file that MLflow packages and deploys. When Databricks Model Serving
loads this file, it:
1. Initializes the LLM (free Llama 3.3 70B)
2. Registers all tools (UC Functions + Vector Search)
3. Builds the LangGraph agent
4. Wraps it in LangGraphResponsesAgent for Responses API compatibility
5. Sets it as the active MLflow model

Free Databricks Models available:
- databricks-meta-llama-3-3-70b-instruct (used here)
- databricks-meta-llama-3-1-405b-instruct
- databricks-dbrx-instruct
"""

import json
from typing import Annotated, Any, Generator, Optional, Sequence, TypedDict, Union
from uuid import uuid4

import mlflow
from databricks_langchain import (
    ChatDatabricks,
    UCFunctionToolkit,
    VectorSearchRetrieverTool,
)
from langchain_core.language_models import LanguageModelLike
from langchain_core.messages import (
    AIMessage,
    AIMessageChunk,
    BaseMessage,
    convert_to_openai_messages,
)
from langchain_core.runnables import RunnableConfig, RunnableLambda
from langchain_core.tools import BaseTool
from langgraph.graph import END, StateGraph
from langgraph.graph.message import add_messages
from langgraph.prebuilt.tool_node import ToolNode
from mlflow.entities import SpanType
from mlflow.pyfunc import ResponsesAgent
from mlflow.types.responses import (
    ResponsesAgentRequest,
    ResponsesAgentResponse,
    ResponsesAgentStreamEvent,
)

# ============================================================
# LLM Configuration - Using FREE Databricks Foundation Model
# ============================================================
LLM_ENDPOINT_NAME = "databricks-meta-llama-3-3-70b-instruct"
llm = ChatDatabricks(endpoint=LLM_ENDPOINT_NAME)

# ============================================================
# Tools Configuration
# ============================================================
tools = []

# Unity Catalog Function Tools (Orders + Escalation)
UC_TOOL_NAMES = [
    "agents.escalation.escalate_to_human",
    "agents.orders_data.cancel_order",
    "agents.orders_data.get_all_orders",
    "agents.orders_data.get_order_details",
    "agents.orders_data.get_order_status",
]
uc_toolkit = UCFunctionToolkit(function_names=UC_TOOL_NAMES)
tools.extend(uc_toolkit.tools)

# Vector Search Retriever Tool (Policy RAG)
VECTOR_SEARCH_TOOL = VectorSearchRetrieverTool(
    index_name="agents.main.foodly_policy_embedding_index",
    tool_name="foodly_policy_document_retrieval_tool",
    num_results=2,
    tool_description=(
        "Use this tool to search the Foodly knowledge base for policies, "
        "procedures, and service-related information. It retrieves the most "
        "relevant chunks from the company's official documentation, including "
        "refund rules, cancellation terms, delivery guidelines, loyalty program "
        "details, privacy policies, and escalation procedures"
    ),
)
tools.append(VECTOR_SEARCH_TOOL)

# ============================================================
# System Prompt
# ============================================================
system_prompt = """
You are Foodly Support Agent.

You handle all user questions and issues related to Foodly:
- Orders: list, check status, show details, cancel
- Policies: refunds, cancellations, loyalty, delivery, safety, privacy, promotions
- Refunds: initiate or check status
- Escalation: when user requests a human

Use the provided tools to fetch or update information.
Never make up answers.
If a tool call fails or required information (like order ID or user ID) is missing,
ask the user for what's missing and wait for their reply.
Only escalate when the user explicitly asks for a human or when no tool can solve the issue.

Keep replies short, clear, friendly, and safe.
"""

# ============================================================
# Build and Register the Agent
# ============================================================
from helpers import LangGraphResponsesAgent, create_tool_calling_agent

mlflow.langchain.autolog()
agent = create_tool_calling_agent(llm, tools, system_prompt)
AGENT = LangGraphResponsesAgent(agent)
mlflow.models.set_model(AGENT)
