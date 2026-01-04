"""
State Management for Agentic Fraud Detection
"""

from typing import TypedDict, List, Dict, Optional, Any, Annotated
from dataclasses import dataclass, field
from datetime import datetime
import operator


@dataclass
class StepResult:
    """Result of a single step execution."""
    step_id: str
    step_description: str
    sql_query: str
    sql_approved: bool = False
    sql_edited: bool = False
    execution_result: Optional[List[Dict]] = None
    execution_error: Optional[str] = None
    row_count: int = 0
    feedback: Optional[str] = None
    timestamp: datetime = field(default_factory=datetime.now)


@dataclass
class PatternState:
    """State for pattern processing."""
    pattern_id: str
    pattern_name: str
    description: str
    detection_logic: Dict[str, str]
    
    # Current processing state
    current_step: int = 0
    total_steps: int = 0
    
    # Step results
    step_results: List[StepResult] = field(default_factory=list)
    
    # Final SQL function
    final_function: Optional[str] = None
    final_function_name: Optional[str] = None
    
    # Final execution
    final_result: Optional[List[Dict]] = None
    final_error: Optional[str] = None
    final_approved: bool = False
    
    # Tool insertion
    tool_id: Optional[str] = None
    tool_inserted: bool = False
    
    # Status
    status: str = "pending"  # pending, processing, completed, failed
    error_message: Optional[str] = None


class AgentState(TypedDict):
    """LangGraph agent state."""
    
    # Pattern information
    pattern_id: str
    pattern_name: str
    pattern_description: str
    detection_logic: Dict[str, str]
    
    # Step tracking
    steps: List[str]
    current_step_index: int
    total_steps: int
    
    # SQL storage
    step_sql_queries: Annotated[List[Dict], operator.add]  # Accumulate SQL queries
    
    # Current step state
    current_step_description: str
    current_sql_query: str
    current_sql_approved: bool
    current_execution_result: Optional[List[Dict]]
    current_execution_error: Optional[str]
    
    # Human feedback
    awaiting_feedback: bool
    feedback_type: str  # "sql_approval", "execution_result", "final_approval"
    user_feedback: str
    user_edit: Optional[str]
    
    # Final function
    final_sql_function: str
    final_function_name: str
    
    # Final result
    final_result: Optional[List[Dict]]
    final_error: Optional[str]
    final_approved: bool
    
    # Tool insertion
    tool_id: str
    tool_inserted: bool
    
    # Messages for LLM
    messages: Annotated[List[Dict], operator.add]
    
    # Status
    status: str
    error: Optional[str]


def create_initial_state(pattern: Dict) -> AgentState:
    """Create initial agent state from pattern."""
    detection_logic = pattern.get("detection_logic", {})
    steps = list(detection_logic.values())
    
    return AgentState(
        pattern_id=pattern["pattern_id"],
        pattern_name=pattern["pattern_name"],
        pattern_description=pattern.get("description", pattern.get("nlp_description", "")),
        detection_logic=detection_logic,
        
        steps=steps,
        current_step_index=0,
        total_steps=len(steps),
        
        step_sql_queries=[],
        
        current_step_description="",
        current_sql_query="",
        current_sql_approved=False,
        current_execution_result=None,
        current_execution_error=None,
        
        awaiting_feedback=False,
        feedback_type="",
        user_feedback="",
        user_edit=None,
        
        final_sql_function="",
        final_function_name="",
        
        final_result=None,
        final_error=None,
        final_approved=False,
        
        tool_id="",
        tool_inserted=False,
        
        messages=[],
        
        status="pending",
        error=None
    )

