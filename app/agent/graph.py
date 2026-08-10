from langgraph.graph import END, START, StateGraph

from app.agent.nodes import (
    classify_intent,
    confirm_order,
    extract_order_items,
    generate_reply,
    validate_order_items,
)
from app.agent.state import AgentState


def _route_after_validation(state: AgentState) -> str:
    return "confirm_order" if state["intent"] == "CONFIRM" else "generate_reply"


def build_graph():
    graph = StateGraph(AgentState)

    graph.add_node("classify_intent", classify_intent)
    graph.add_node("extract_order_items", extract_order_items)
    graph.add_node("validate_order_items", validate_order_items)
    graph.add_node("generate_reply", generate_reply)
    graph.add_node("confirm_order", confirm_order)

    graph.add_edge(START, "classify_intent")
    graph.add_edge("classify_intent", "extract_order_items")
    graph.add_edge("extract_order_items", "validate_order_items")
    graph.add_conditional_edges(
        "validate_order_items",
        _route_after_validation,
        {"confirm_order": "confirm_order", "generate_reply": "generate_reply"},
    )
    graph.add_edge("generate_reply", END)
    graph.add_edge("confirm_order", END)

    return graph.compile()


order_agent = build_graph()
