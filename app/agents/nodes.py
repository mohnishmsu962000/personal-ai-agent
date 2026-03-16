import structlog
from langchain_openai import ChatOpenAI
from langchain_core.messages import HumanMessage, SystemMessage
import json

from app.config import get_settings
from app.agents.state import AgentState
from app.schemas.agent import ParsedIntent, IntentType, CalendarEvent, NotionTask
from app.tools.calendar import create_calendar_event
from app.tools.notion import create_task
from app.tools.telegram import send_message

logger = structlog.get_logger()
settings = get_settings()

def get_llm():
    s = get_settings()
    return ChatOpenAI(
        model=s.openai_model,
        api_key=s.openai_api_key,
        temperature=0,
    )

PARSE_SYSTEM_PROMPT = """
You are an AI assistant that parses natural language messages and extracts structured intent.

You must return a JSON object with these exact fields:
- intent: one of "create_event", "create_task", "get_summary", "unknown"
- title: string, the title of the event or task
- date: string in YYYY-MM-DD format, or null if not mentioned
- time: string in HH:MM format, or null if not mentioned
- priority: one of "High", "Medium", "Low", or null
- notes: any additional context, or null

Today's date is {today}.

Examples:
- "Dentist appointment Thursday 3pm" -> create_event
- "Buy groceries this week" -> create_task
- "Remind me to call mom tomorrow" -> create_task
- "What's on my schedule?" -> get_summary

Return only valid JSON, no explanation, no markdown.
"""


async def parse_intent_node(state: AgentState) -> AgentState:
    log = logger.bind(message=state["raw_message"])
    log.info("parsing_intent")

    try:
        from datetime import date
        today = date.today().isoformat()

        messages = [
            SystemMessage(content=PARSE_SYSTEM_PROMPT.format(today=today)),
            HumanMessage(content=state["raw_message"]),
        ]

        response = await get_llm().ainvoke(messages)
        parsed_dict = json.loads(response.content)
        parsed = ParsedIntent(**parsed_dict)

        log.info("intent_parsed", intent=parsed.intent)

        return {
            **state,
            "intent": parsed.intent,
            "parsed": parsed,
            "error": None,
        }

    except Exception as e:
        log.error("parse_failed", error=str(e))
        return {
            **state,
            "intent": IntentType.UNKNOWN,
            "error": str(e),
        }


async def create_event_node(state: AgentState) -> AgentState:
    log = logger.bind(title=state["parsed"].title)
    log.info("creating_event")

    try:
        parsed = state["parsed"]
        event = CalendarEvent(
            title=parsed.title,
            date=parsed.date,
            time=parsed.time,
            description=parsed.notes,
        )

        result = await create_calendar_event(event)

        if result["success"]:
            response = (
                f"✅ Event created: *{parsed.title}*\n"
                f"📅 {parsed.date}"
                + (f" at {parsed.time}" if parsed.time else "")
            )
        else:
            response = f"❌ Failed to create event: {result.get('error')}"

        return {
            **state,
            "tool_result": result,
            "response_message": response,
            "success": result["success"],
        }

    except Exception as e:
        log.error("create_event_failed", error=str(e))
        return {
            **state,
            "error": str(e),
            "response_message": f"❌ Failed to create event: {str(e)}",
            "success": False,
        }


async def create_task_node(state: AgentState) -> AgentState:
    log = logger.bind(title=state["parsed"].title)
    log.info("creating_task")

    try:
        parsed = state["parsed"]
        task = NotionTask(
            title=parsed.title,
            priority=parsed.priority or "Medium",
            due_date=parsed.date,
            source="Telegram",
        )

        result = await create_task(task)

        if result["success"]:
            response = (
                f"✅ Task created: *{parsed.title}*\n"
                f"🎯 Priority: {task.priority}"
                + (f"\n📅 Due: {parsed.date}" if parsed.date else "")
            )
        else:
            response = f"❌ Failed to create task: {result.get('error')}"

        return {
            **state,
            "tool_result": result,
            "response_message": response,
            "success": result["success"],
        }

    except Exception as e:
        log.error("create_task_failed", error=str(e))
        return {
            **state,
            "error": str(e),
            "response_message": f"❌ Failed to create task: {str(e)}",
            "success": False,
        }


async def unknown_intent_node(state: AgentState) -> AgentState:
    return {
        **state,
        "response_message": (
            "🤔 I didn't understand that. Try:\n"
            "• 'Dentist appointment Thursday 3pm'\n"
            "• 'Buy groceries this week'\n"
            "• 'Call mom tomorrow high priority'"
        ),
        "success": False,
    }


async def send_response_node(state: AgentState) -> AgentState:
    await send_message(state["user_id"], state["response_message"])
    return state