import structlog
from langgraph.graph import StateGraph, END

from app.agents.state import AgentState
from app.agents.nodes import (
    parse_intent_node,
    create_event_node,
    create_task_node,
    unknown_intent_node,
    send_response_node,
)
from app.schemas.agent import IntentType

logger = structlog.get_logger()


def route_intent(state: AgentState) -> str:
    """Router function — decides which node to go to based on parsed intent."""
    intent = state.get("intent")

    if intent == IntentType.CREATE_EVENT:
        return "create_event"
    elif intent == IntentType.CREATE_TASK:
        return "create_task"
    else:
        return "unknown_intent"


def build_graph() -> StateGraph:
    graph = StateGraph(AgentState)

    # Add all nodes
    graph.add_node("parse_intent", parse_intent_node)
    graph.add_node("create_event", create_event_node)
    graph.add_node("create_task", create_task_node)
    graph.add_node("unknown_intent", unknown_intent_node)
    graph.add_node("send_response", send_response_node)

    # Entry point
    graph.set_entry_point("parse_intent")

    # Conditional routing after parsing
    graph.add_conditional_edges(
        "parse_intent",
        route_intent,
        {
            "create_event": "create_event",
            "create_task": "create_task",
            "unknown_intent": "unknown_intent",
        }
    )

    # All action nodes flow into send_response
    graph.add_edge("create_event", "send_response")
    graph.add_edge("create_task", "send_response")
    graph.add_edge("unknown_intent", "send_response")

    # send_response is the end
    graph.add_edge("send_response", END)

    return graph.compile()


# Single compiled graph instance
agent_graph = build_graph()


async def run_agent(message: str, user_id: int) -> dict:
    log = logger.bind(message=message, user_id=user_id)
    log.info("agent_started")

    initial_state: AgentState = {
        "raw_message": message,
        "user_id": user_id,
        "intent": None,
        "parsed": None,
        "tool_result": None,
        "error": None,
        "response_message": "",
        "success": False,
    }

    result = await agent_graph.ainvoke(initial_state)

    log.info(
        "agent_completed",
        intent=result.get("intent"),
        success=result.get("success"),
    )

    return result