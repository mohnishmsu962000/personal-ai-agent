import structlog
from datetime import datetime
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from google.auth.transport.requests import Request
from googleapiclient.discovery import build
from pathlib import Path

from app.config import get_settings
from app.schemas.agent import CalendarEvent

logger = structlog.get_logger()
settings = get_settings()

SCOPES = ["https://www.googleapis.com/auth/calendar"]


def _get_calendar_service():
    creds = None
    token_path = Path(settings.google_token_path)
    credentials_path = Path(settings.google_credentials_path)

    if token_path.exists():
        creds = Credentials.from_authorized_user_file(str(token_path), SCOPES)

    if not creds or not creds.valid:
        if creds and creds.expired and creds.refresh_token:
            creds.refresh(Request())
        else:
            flow = InstalledAppFlow.from_client_secrets_file(
                str(credentials_path), SCOPES
            )
            creds = flow.run_local_server(port=0)

        with open(str(token_path), "w") as token:
            token.write(creds.to_json())

    return build("calendar", "v3", credentials=creds)


async def create_calendar_event(event: CalendarEvent) -> dict:
    log = logger.bind(title=event.title, date=event.date)

    try:
        service = _get_calendar_service()

        start_datetime = f"{event.date}T{event.time or '09:00'}:00"
        end_datetime = f"{event.date}T{event.time or '10:00'}:00"

        event_body = {
            "summary": event.title,
            "description": event.description or "",
            "start": {
                "dateTime": start_datetime,
                "timeZone": "Asia/Kolkata",
            },
            "end": {
                "dateTime": end_datetime,
                "timeZone": "Asia/Kolkata",
            },
        }

        result = service.events().insert(
            calendarId=settings.google_calendar_id,
            body=event_body,
        ).execute()

        log.info("calendar_event_created", event_id=result.get("id"))

        return {
            "success": True,
            "event_id": result.get("id"),
            "event_link": result.get("htmlLink"),
            "title": event.title,
            "date": event.date,
            "time": event.time,
        }

    except Exception as e:
        log.error("calendar_event_failed", error=str(e))
        return {"success": False, "error": str(e)}


async def get_upcoming_events(days: int = 7) -> list[dict]:
    try:
        service = _get_calendar_service()

        now = datetime.utcnow().isoformat() + "Z"

        result = service.events().list(
            calendarId=settings.google_calendar_id,
            timeMin=now,
            maxResults=10,
            singleEvents=True,
            orderBy="startTime",
        ).execute()

        events = result.get("items", [])

        return [
            {
                "title": e.get("summary", "No title"),
                "start": e.get("start", {}).get("dateTime", e.get("start", {}).get("date")),
                "link": e.get("htmlLink"),
            }
            for e in events
        ]

    except Exception as e:
        logger.error("get_events_failed", error=str(e))
        return []