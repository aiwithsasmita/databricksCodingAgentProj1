"""
Genie Tool - Wrapper for Databricks Genie SQL generation
"""

import time
from typing import Tuple, Optional
from databricks.sdk import WorkspaceClient
from databricks.sdk.service.dashboards import GenieMessage


class GenieTool:
    """
    Databricks Genie tool for converting natural language to SQL.
    """
    
    def __init__(self, host: str, token: str, space_id: str):
        """
        Initialize Genie tool.
        
        Args:
            host: Databricks workspace URL
            token: Databricks access token
            space_id: Genie space ID
        """
        self.host = host
        self.token = token
        self.space_id = space_id
        self.client = WorkspaceClient(host=host, token=token)
        self.conversation_id = None
    
    def start_conversation(self) -> str:
        """Start a new Genie conversation."""
        response = self.client.genie.start_conversation(
            space_id=self.space_id,
            content="Hello, I need help generating SQL queries for fraud detection."
        )
        self.conversation_id = response.conversation_id
        return self.conversation_id
    
    def generate_sql(self, prompt: str, max_retries: int = 30, retry_delay: float = 2.0) -> Tuple[str, Optional[str]]:
        """
        Generate SQL from natural language prompt.
        
        Args:
            prompt: Natural language description of the query
            max_retries: Maximum number of retries while waiting for response
            retry_delay: Delay between retries in seconds
            
        Returns:
            Tuple of (sql_query, error_message)
        """
        try:
            # Start conversation if not already started
            if not self.conversation_id:
                self.start_conversation()
            
            # Send message to Genie
            response = self.client.genie.create_message(
                space_id=self.space_id,
                conversation_id=self.conversation_id,
                content=prompt
            )
            
            message_id = response.message_id
            
            # Poll for response
            for _ in range(max_retries):
                message = self.client.genie.get_message(
                    space_id=self.space_id,
                    conversation_id=self.conversation_id,
                    message_id=message_id
                )
                
                if message.status in ["COMPLETED", "FAILED"]:
                    break
                
                time.sleep(retry_delay)
            
            # Extract SQL from response
            if message.status == "COMPLETED" and message.attachments:
                for attachment in message.attachments:
                    if hasattr(attachment, 'query') and attachment.query:
                        sql_query = attachment.query.query
                        if sql_query:
                            return sql_query.strip(), None
            
            # Check for text response
            if message.status == "COMPLETED":
                return "", "No SQL query generated. Genie provided text response only."
            
            return "", f"Genie request failed with status: {message.status}"
            
        except Exception as e:
            return "", f"Genie error: {str(e)}"
    
    def validate_sql(self, sql_query: str) -> Tuple[bool, Optional[str]]:
        """
        Validate SQL query syntax.
        
        Args:
            sql_query: SQL query to validate
            
        Returns:
            Tuple of (is_valid, error_message)
        """
        if not sql_query or not sql_query.strip():
            return False, "Empty SQL query"
        
        # Basic validation
        sql_upper = sql_query.upper().strip()
        
        if not sql_upper.startswith("SELECT"):
            return False, "Query must start with SELECT"
        
        if "FROM" not in sql_upper:
            return False, "Query must contain FROM clause"
        
        return True, None


def create_genie_tool(config) -> GenieTool:
    """Create a Genie tool from config."""
    return GenieTool(
        host=config.databricks_host,
        token=config.databricks_token,
        space_id=config.genie_space_id
    )

