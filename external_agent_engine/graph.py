from langgraph.graph import StateGraph, END
from external_agent_engine.graph_state import WorkflowState
from external_agent_engine.nodes import researcher_node, writer_node, qa_node, publisher_node, database_node

def build_automation_graph():
    """
    Wires the nodes together into a deterministic state machine.
    This acts as the 'invisible factory belt' for our automation.
    """
    print("🏗️ Compiling Workflow Automation Graph...")
    
    # 1. Initialize the Graph with our Brain (State)
    workflow = StateGraph(WorkflowState)

    # 2. Add our Workers (Nodes) to the graph
    workflow.add_node("researcher", researcher_node)
    workflow.add_node("writer", writer_node)
    workflow.add_node("qa_reviewer", qa_node)
    workflow.add_node("publisher", publisher_node)
    workflow.add_node("database", database_node) # 🔴 ADDED DATABASE NODE

    workflow.set_entry_point("researcher")

    # 4. Define the Routing Logic
    def route_action(state: WorkflowState):
        action = state.get("next_action")
        if action == "draft_report":
            return "writer"
        elif action == "review_draft":
            return "qa_reviewer"
        elif action == "publish":
            return "publisher"
        elif action == "archive_data": 
            return "database" # 🔴 ROUTE TO DATABASE
        return END

    # 5. Connect the nodes with Conditional Edges
    workflow.add_conditional_edges("researcher", route_action)
    workflow.add_edge("writer", "qa_reviewer")
    workflow.add_conditional_edges("qa_reviewer", route_action)
    
    # The Publisher now hands off to the Database
    workflow.add_edge("publisher", "database")
    
    # The Database is now the absolute end of the line
    workflow.add_edge("database", END)

    # 5. Compile the engine into an executable application
    app = workflow.compile()
    return app

# --- Quick Test Execution ---
if __name__ == "__main__":
    # This allows us to test the background automation right here in the terminal
    automation_app = build_automation_graph()
    
    initial_state = {
        "user_objective": "Research the latest news and stock performance of TSLA (Tesla) from this week.",
        "messages": [],
        "workspace_data": {},
        "next_action": ""
    }
    
    print("\n🚀 Starting Background Automation...")
    # .invoke() runs the entire graph from start to finish automatically
    final_state = automation_app.invoke(initial_state)
    
    print("\n✅ Automation Complete. Final Output:\n")
    # Print the very last message appended to the state by the Writer Node
    print(final_state["messages"][-1].content)