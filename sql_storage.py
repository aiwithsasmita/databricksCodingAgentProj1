"""
SQL Storage - Store and manage SQL queries during execution
"""

import os
from pathlib import Path
from datetime import datetime
from typing import List, Dict, Optional


class SQLStorage:
    """
    Storage for SQL queries generated during pattern execution.
    Writes to a markdown file for easy review.
    """
    
    def __init__(self, output_dir: str = "./output", filename: str = "sqlcode.md"):
        """
        Initialize SQL storage.
        
        Args:
            output_dir: Directory to store the SQL file
            filename: Name of the SQL markdown file
        """
        self.output_dir = Path(output_dir)
        self.filename = filename
        self.filepath = self.output_dir / filename
        
        # Create output directory if not exists
        self.output_dir.mkdir(parents=True, exist_ok=True)
        
        # In-memory storage
        self.step_queries: List[Dict] = []
        self.final_function: Optional[str] = None
    
    def add_step_query(self, step_id: str, step_description: str, sql_query: str, 
                       approved: bool = False, edited: bool = False):
        """
        Add a step query to storage.
        
        Args:
            step_id: Identifier for the step
            step_description: Description of what the step does
            sql_query: The SQL query for this step
            approved: Whether the query was approved by user
            edited: Whether the query was edited by user
        """
        self.step_queries.append({
            "step_id": step_id,
            "step_description": step_description,
            "sql_query": sql_query,
            "approved": approved,
            "edited": edited,
            "timestamp": datetime.now().isoformat()
        })
        
        # Write to file
        self._write_to_file()
    
    def update_step_query(self, step_id: str, sql_query: str, edited: bool = True):
        """
        Update an existing step query.
        
        Args:
            step_id: Identifier for the step
            sql_query: The updated SQL query
            edited: Mark as edited
        """
        for step in self.step_queries:
            if step["step_id"] == step_id:
                step["sql_query"] = sql_query
                step["edited"] = edited
                step["timestamp"] = datetime.now().isoformat()
                break
        
        self._write_to_file()
    
    def set_final_function(self, function_sql: str, function_name: str):
        """
        Set the final combined SQL function.
        
        Args:
            function_sql: The complete SQL function
            function_name: Name of the function
        """
        self.final_function = {
            "name": function_name,
            "sql": function_sql,
            "timestamp": datetime.now().isoformat()
        }
        
        self._write_to_file()
    
    def get_all_queries(self) -> List[Dict]:
        """Get all stored step queries."""
        return self.step_queries.copy()
    
    def get_final_function(self) -> Optional[Dict]:
        """Get the final function."""
        return self.final_function
    
    def clear(self):
        """Clear all stored queries."""
        self.step_queries = []
        self.final_function = None
        
        # Delete file if exists
        if self.filepath.exists():
            self.filepath.unlink()
    
    def _write_to_file(self):
        """Write all queries to the markdown file."""
        content = []
        
        # Header
        content.append("# SQL Code Storage")
        content.append(f"\nGenerated at: {datetime.now().isoformat()}\n")
        
        # Step queries
        content.append("## Step Queries\n")
        
        for i, step in enumerate(self.step_queries, 1):
            status = "✅ Approved" if step["approved"] else "⏳ Pending"
            edited = " (Edited)" if step["edited"] else ""
            
            content.append(f"### Step {i}: {step['step_id']}{edited}")
            content.append(f"\n**Description:** {step['step_description']}")
            content.append(f"\n**Status:** {status}")
            content.append(f"\n**Timestamp:** {step['timestamp']}")
            content.append(f"\n```sql\n{step['sql_query']}\n```\n")
        
        # Final function
        if self.final_function:
            content.append("## Final Combined Function\n")
            content.append(f"**Function Name:** {self.final_function['name']}")
            content.append(f"\n**Timestamp:** {self.final_function['timestamp']}")
            content.append(f"\n```sql\n{self.final_function['sql']}\n```\n")
        
        # Write to file
        with open(self.filepath, 'w', encoding='utf-8') as f:
            f.write('\n'.join(content))
    
    def load_from_file(self) -> bool:
        """
        Load queries from file (for recovery).
        
        Returns:
            True if file was loaded successfully
        """
        if not self.filepath.exists():
            return False
        
        # For now, just verify file exists
        # Full parsing would require more complex logic
        return True


