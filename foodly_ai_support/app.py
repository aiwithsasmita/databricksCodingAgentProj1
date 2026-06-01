"""
Foodly AI Support - Streamlit Chat UI

This app connects to the deployed Foodly agent on Databricks Model Serving
and provides a beautiful chat interface for customer support.

Two modes:
1. DEPLOYED MODE: Connects to a Databricks Model Serving endpoint (production)
2. DEMO MODE: Simulates responses locally for testing the UI without Databricks

Setup:
    pip install streamlit databricks-sdk
    streamlit run app.py
"""

import os
import json
import streamlit as st
from datetime import datetime

# ============================================================
# Page Configuration
# ============================================================
st.set_page_config(
    page_title="Foodly AI Support",
    page_icon="🍕",
    layout="centered",
    initial_sidebar_state="expanded",
)

# ============================================================
# Custom CSS for a modern chat UI
# ============================================================
st.markdown("""
<style>
    .main-header {
        text-align: center;
        padding: 1rem 0;
        border-bottom: 2px solid #ff6b35;
        margin-bottom: 1.5rem;
    }
    .main-header h1 {
        color: #ff6b35;
        font-size: 2.2rem;
        margin-bottom: 0.3rem;
    }
    .main-header p {
        color: #666;
        font-size: 1rem;
    }
    .tool-badge {
        display: inline-block;
        padding: 2px 8px;
        border-radius: 12px;
        font-size: 0.75rem;
        font-weight: 600;
        margin: 2px;
    }
    .tool-policy { background: #e3f2fd; color: #1565c0; }
    .tool-order { background: #e8f5e9; color: #2e7d32; }
    .tool-escalation { background: #fff3e0; color: #e65100; }
    .status-connected { color: #4caf50; }
    .status-demo { color: #ff9800; }
    .sidebar-info {
        background: #f8f9fa;
        padding: 1rem;
        border-radius: 8px;
        margin: 0.5rem 0;
        border-left: 3px solid #ff6b35;
    }
    .stChatMessage {
        border-radius: 12px;
    }
</style>
""", unsafe_allow_html=True)

# ============================================================
# Sidebar Configuration
# ============================================================
with st.sidebar:
    st.markdown("## Settings")

    mode = st.radio(
        "Mode",
        ["Demo (No Databricks needed)", "Connected (Databricks endpoint)"],
        index=0,
    )

    if mode == "Connected (Databricks endpoint)":
        st.markdown("---")
        st.markdown("### Databricks Connection")
        databricks_host = st.text_input(
            "Workspace URL",
            value=os.environ.get("DATABRICKS_HOST", ""),
            placeholder="https://your-workspace.databricks.com",
        )
        databricks_token = st.text_input(
            "Access Token",
            value=os.environ.get("DATABRICKS_TOKEN", ""),
            type="password",
            placeholder="dapi...",
        )
        endpoint_name = st.text_input(
            "Serving Endpoint Name",
            value="agents-main-foodly-ai-assistant",
            placeholder="your-endpoint-name",
        )
        is_connected = bool(databricks_host and databricks_token and endpoint_name)
        if is_connected:
            st.markdown('<p class="status-connected">Connected</p>', unsafe_allow_html=True)
        else:
            st.warning("Fill in all fields to connect.")
    else:
        is_connected = False

    st.markdown("---")
    st.markdown("### Agent Capabilities")
    st.markdown("""
    <div class="sidebar-info">
        <span class="tool-badge tool-policy">Policy RAG</span>
        <span class="tool-badge tool-order">Orders</span>
        <span class="tool-badge tool-escalation">Escalation</span>
        <br><br>
        <b>6 Tools Available:</b>
        <ul style="font-size:0.85rem; margin:0.5rem 0;">
            <li>Policy Document Search</li>
            <li>Get All Orders</li>
            <li>Get Order Status</li>
            <li>Get Order Details</li>
            <li>Cancel Order</li>
            <li>Escalate to Human</li>
        </ul>
    </div>
    """, unsafe_allow_html=True)

    st.markdown("---")
    st.markdown("### Architecture")
    st.markdown("""
    ```
    User Message
        |
    LLM (Llama 3.3 70B)
        |
    Tool Selection
       / | \\
    RAG  UC   UC
    (VS) (Ord) (Esc)
        |
    Final Response
    ```
    """)

    if st.button("Clear Chat", use_container_width=True):
        st.session_state.messages = []
        st.rerun()

# ============================================================
# Header
# ============================================================
st.markdown("""
<div class="main-header">
    <h1>Foodly AI Support</h1>
    <p>Powered by Databricks Agent Framework + LangGraph + Llama 3.3 70B</p>
</div>
""", unsafe_allow_html=True)

# ============================================================
# Demo responses for testing UI without Databricks
# ============================================================
DEMO_RESPONSES = {
    "refund": (
        "Based on Foodly's official policy, here's what I found about refunds:\n\n"
        "**Refund Policy:**\n"
        "- Full refund if order is cancelled before preparation begins\n"
        "- 50% refund if cancelled during preparation\n"
        "- No refund once the order is out for delivery\n"
        "- Quality issues: Full refund with photo evidence within 2 hours\n\n"
        "Would you like to initiate a refund for a specific order?"
    ),
    "order": (
        "I'd be happy to help you with your order! I found the following orders for your account:\n\n"
        "| Order ID | Restaurant | Status | ETA |\n"
        "|----------|-----------|--------|-----|\n"
        "| ORD001 | Pizza Palace | Placed | 25 min |\n"
        "| ORD002 | Burger Bazaar | Preparing | 30 min |\n\n"
        "Which order would you like to know more about?"
    ),
    "cancel": (
        "I've processed the cancellation for your order:\n\n"
        "- **Order:** ORD001 (Pizza Palace)\n"
        "- **Status:** Cancelled Successfully\n"
        "- **Refund:** Rs. 599.00 initiated\n"
        "- **Refund ETA:** 3-5 business days\n\n"
        "Is there anything else I can help with?"
    ),
    "status": (
        "Here's the current status of your order:\n\n"
        "- **Order ID:** ORD003\n"
        "- **Restaurant:** Curry Corner\n"
        "- **Status:** Out for Delivery\n"
        "- **ETA:** 15 minutes\n"
        "- **Rider:** Mahesh\n\n"
        "Your food is on its way! The rider is nearby."
    ),
    "human": (
        "I've escalated your issue to our support team.\n\n"
        "- **Ticket ID:** TCK-847293\n"
        "- **Expected Response:** Within 30 minutes\n"
        "- **Priority:** High\n\n"
        "A human support specialist will reach out to you shortly. "
        "Is there anything else I can help with in the meantime?"
    ),
    "default": (
        "I'm Foodly's AI Support Agent! I can help you with:\n\n"
        "- **Orders** - Check status, view details, cancel orders\n"
        "- **Policies** - Refunds, delivery, privacy, loyalty programs\n"
        "- **Escalation** - Connect you with a human agent\n\n"
        "What would you like help with today?"
    ),
}


def get_demo_response(user_message: str) -> str:
    """Match user input to a demo response based on keywords."""
    msg = user_message.lower()
    if any(w in msg for w in ["refund", "return", "money back", "policy"]):
        return DEMO_RESPONSES["refund"]
    elif any(w in msg for w in ["cancel", "cancellation"]):
        return DEMO_RESPONSES["cancel"]
    elif any(w in msg for w in ["status", "where", "track", "eta"]):
        return DEMO_RESPONSES["status"]
    elif any(w in msg for w in ["order", "list", "my orders"]):
        return DEMO_RESPONSES["order"]
    elif any(w in msg for w in ["human", "agent", "person", "escalate", "talk to"]):
        return DEMO_RESPONSES["human"]
    else:
        return DEMO_RESPONSES["default"]


def call_databricks_endpoint(user_message: str, history: list) -> str:
    """Call the deployed Databricks Model Serving endpoint."""
    try:
        from databricks.sdk import WorkspaceClient

        w = WorkspaceClient(
            host=databricks_host,
            token=databricks_token,
        )

        messages = []
        for msg in history:
            messages.append({"role": msg["role"], "content": msg["content"]})
        messages.append({"role": "user", "content": user_message})

        response = w.serving_endpoints.query(
            name=endpoint_name,
            input=messages,
        )

        if hasattr(response, "output") and response.output:
            for item in response.output:
                if hasattr(item, "content"):
                    for content in item.content:
                        if hasattr(content, "text"):
                            return content.text
                elif hasattr(item, "text"):
                    return item.text

        return str(response)

    except ImportError:
        return (
            "The `databricks-sdk` package is required for connected mode. "
            "Install it with: `pip install databricks-sdk`"
        )
    except Exception as e:
        return f"Error connecting to Databricks: {str(e)}"


# ============================================================
# Chat Logic
# ============================================================
if "messages" not in st.session_state:
    st.session_state.messages = []

for message in st.session_state.messages:
    avatar = "🍕" if message["role"] == "assistant" else "👤"
    with st.chat_message(message["role"], avatar=avatar):
        st.markdown(message["content"])

if not st.session_state.messages:
    with st.chat_message("assistant", avatar="🍕"):
        welcome = (
            "Welcome to **Foodly Support**! I'm your AI assistant.\n\n"
            "I can help you with:\n"
            "- Checking your **order status** and details\n"
            "- Understanding our **policies** (refunds, delivery, etc.)\n"
            "- **Cancelling** orders\n"
            "- **Escalating** to a human agent\n\n"
            "How can I help you today?"
        )
        st.markdown(welcome)

if prompt := st.chat_input("Ask about your order, policies, or anything Foodly..."):
    st.session_state.messages.append({"role": "user", "content": prompt})
    with st.chat_message("user", avatar="👤"):
        st.markdown(prompt)

    with st.chat_message("assistant", avatar="🍕"):
        with st.spinner("Thinking..."):
            if is_connected:
                response = call_databricks_endpoint(prompt, st.session_state.messages[:-1])
            else:
                response = get_demo_response(prompt)

        st.markdown(response)

    st.session_state.messages.append({"role": "assistant", "content": response})

# ============================================================
# Footer with Quick Actions
# ============================================================
st.markdown("---")
cols = st.columns(4)
quick_actions = [
    ("Where is my order?", "📦"),
    ("Refund policy", "💰"),
    ("Cancel order", "❌"),
    ("Talk to human", "👤"),
]
for col, (action, icon) in zip(cols, quick_actions):
    if col.button(f"{icon} {action}", use_container_width=True):
        st.session_state.messages.append({"role": "user", "content": action})
        st.rerun()
