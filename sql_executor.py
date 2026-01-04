"""
SQL Executor - Execute SQL queries against Databricks
"""

from typing import List, Dict, Tuple, Optional
from databricks import sql as dbsql


class SQLExecutor:
    """
    Execute SQL queries against Databricks SQL Warehouse.
    """
    
    def __init__(self, server_hostname: str, http_path: str, access_token: str):
        """
        Initialize SQL executor.
        
        Args:
            server_hostname: Databricks SQL warehouse hostname
            http_path: HTTP path for the warehouse
            access_token: Databricks access token
        """
        self.server_hostname = server_hostname
        self.http_path = http_path
        self.access_token = access_token
    
    def execute(self, sql_query: str, limit: int = 50) -> Tuple[List[str], List[tuple], Optional[str]]:
        """
        Execute a SQL query.
        
        Args:
            sql_query: SQL query to execute
            limit: Maximum number of rows to return
            
        Returns:
            Tuple of (column_names, rows, error_message)
        """
        try:
            with dbsql.connect(
                server_hostname=self.server_hostname,
                http_path=self.http_path,
                access_token=self.access_token
            ) as conn:
                with conn.cursor() as cursor:
                    cursor.execute(sql_query)
                    
                    # Get column names
                    columns = [desc[0] for desc in cursor.description] if cursor.description else []
                    
                    # Fetch rows
                    rows = cursor.fetchmany(limit)
                    
                    return columns, rows, None
                    
        except Exception as e:
            return [], [], str(e)
    
    def execute_and_format(self, sql_query: str, limit: int = 50) -> Tuple[List[Dict], Optional[str]]:
        """
        Execute SQL and return formatted results as list of dicts.
        
        Args:
            sql_query: SQL query to execute
            limit: Maximum number of rows
            
        Returns:
            Tuple of (results_as_dicts, error_message)
        """
        columns, rows, error = self.execute(sql_query, limit)
        
        if error:
            return [], error
        
        results = []
        for row in rows:
            results.append(dict(zip(columns, row)))
        
        return results, None
    
    def insert_tool(self, tool_id: str, pattern_id: str, policy_id: str,
                   sql_query: str, tools_table: str) -> Tuple[bool, Optional[str]]:
        """
        Insert a tool into the tools table.
        
        Args:
            tool_id: Tool identifier
            pattern_id: Pattern this tool belongs to
            policy_id: Policy this tool belongs to
            sql_query: SQL query for the tool
            tools_table: Name of the tools table
            
        Returns:
            Tuple of (success, error_message)
        """
        try:
            with dbsql.connect(
                server_hostname=self.server_hostname,
                http_path=self.http_path,
                access_token=self.access_token
            ) as conn:
                with conn.cursor() as cursor:
                    # First, try to delete existing tool
                    delete_sql = f"DELETE FROM {tools_table} WHERE tool_id = ?"
                    try:
                        cursor.execute(delete_sql, [tool_id])
                    except:
                        pass  # Ignore if doesn't exist
                    
                    # Insert new tool with parameterized query
                    insert_sql = f"""
                        INSERT INTO {tools_table} 
                        (tool_id, pattern_id, policy_id, sql_query, validation_status, 
                         validated_by, validated_at, execution_count, created_at, updated_at)
                        VALUES (?, ?, ?, ?, 'validated', 'agentic_framework', 
                                CURRENT_TIMESTAMP(), 0, CURRENT_TIMESTAMP(), CURRENT_TIMESTAMP())
                    """
                    cursor.execute(insert_sql, [tool_id, pattern_id, policy_id, sql_query])
                    return True, None
                    
        except Exception as e:
            return False, str(e)
    
    def update_pattern_tool(self, pattern_id: str, tool_id: str, 
                           patterns_table: str) -> Tuple[bool, Optional[str]]:
        """
        Update pattern with tool_id reference.
        
        Args:
            pattern_id: Pattern to update
            tool_id: Tool ID to link
            patterns_table: Name of the patterns table
            
        Returns:
            Tuple of (success, error_message)
        """
        update_sql = f"""
            UPDATE {patterns_table}
            SET tool_id = '{tool_id}',
                status = 'active',
                updated_at = CURRENT_TIMESTAMP()
            WHERE pattern_id = '{pattern_id}'
        """
        
        try:
            with dbsql.connect(
                server_hostname=self.server_hostname,
                http_path=self.http_path,
                access_token=self.access_token
            ) as conn:
                with conn.cursor() as cursor:
                    cursor.execute(update_sql)
                    return True, None
                    
        except Exception as e:
            return False, str(e)


def create_sql_executor(config) -> SQLExecutor:
    """Create SQL executor from config."""
    return SQLExecutor(
        server_hostname=config.dbsql_server_hostname,
        http_path=config.dbsql_http_path,
        access_token=config.databricks_token
    )

