from typing import TypedDict, Annotated, Dict, Any
from langgraph.graph.message import add_messages
from langchain_core.messages import BaseMessage

class WorkflowState(TypedDict):
    """
    This defines the memory structure of your automation system.
    Every agent in your workflow will read and update these variables.
    """
    
    # 1. Conversation & Thought History
    # 'add_messages' ensures new messages are appended, not overwritten
    messages: Annotated[list[BaseMessage], add_messages]
    
    # 2. The overarching goal the user wants to achieve
    user_objective: str
    
    # 3. A flexible dictionary to store data across the workflow
    # (e.g., scraped web text, API responses, or intermediate drafts)
    workspace_data: Dict[str, Any]
    
    # 4. A routing flag to tell the graph what to do next
    # (e.g., "needs_research", "ready_to_draft", "finished")
    next_action: str