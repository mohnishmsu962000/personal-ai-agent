from pydantic import BaseModel, Field
from enum import Enum
from typing import Optional
from datetime import datetime


class IntentType(str, Enum):
    CREATE_EVENT = "create_event"
    CREATE_TASK = "create_task"
    GET_SUMMARY = "get_summary"
    UNKNOWN = "unknown"


class ParsedIntent(BaseModel):
    intent: IntentType
    title: str = Field(..., description="Title of the event or task")
    date: Optional[str] = Field(None, description="Date in YYYY-MM-DD format")
    time: Optional[str] = Field(None, description="Time in HH:MM format")
    priority: Optional[str] = Field(None, description="High, Medium or Low")
    notes: Optional[str] = Field(None, description="Any additional notes")


class AgentInput(BaseModel):
    message: str = Field(..., description="Raw message from the user")
    user_id: int = Field(..., description="Telegram user ID")


class AgentOutput(BaseModel):
    success: bool
    message: str
    intent: Optional[IntentType] = None
    data: Optional[dict] = None


class CalendarEvent(BaseModel):
    title: str
    date: str
    time: Optional[str] = None
    description: Optional[str] = None


class NotionTask(BaseModel):
    title: str
    priority: str = "Medium"
    due_date: Optional[str] = None
    source: str = "Telegram"