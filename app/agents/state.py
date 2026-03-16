from typing import TypedDict, Optional
from app.schemas.agent import ParsedIntent, IntentType


class AgentState(TypedDict):
    # Input
    raw_message: str
    user_id: int

    # Parsed intent
    intent: Optional[IntentType]
    parsed: Optional[ParsedIntent]

    # Execution
    tool_result: Optional[dict]
    error: Optional[str]

    # Output
    response_message: str
    success: bool