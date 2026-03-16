# Personal AI Agent

LangGraph-powered personal AI agent that manages tasks, events and reminders across Telegram, Google Calendar and Notion.

## What it does

Send a natural language message on Telegram and the agent will:
- Create a Google Calendar event if it detects an appointment
- Create a Notion task if it detects a to-do
- Send a daily morning summary of upcoming events and pending tasks

## Architecture
```
Telegram message
        ↓
FastAPI webhook
        ↓
LangGraph agent
        ↓
parse_intent_node (GPT-4o extracts intent, date, time, priority)
        ↓
conditional routing
        ↓
create_event_node ──→ Google Calendar API
create_task_node  ──→ Notion API
unknown_intent    ──→ help message
        ↓
send_response_node ──→ Telegram
```

## Agent Graph
```
                    ┌─────────────────┐
                    │   parse_intent  │
                    └────────┬────────┘
                             │
              ┌──────────────┼──────────────┐
              ▼              ▼              ▼
       create_event    create_task   unknown_intent
              │              │              │
              └──────────────┼──────────────┘
                             ▼
                      send_response
                             │
                            END
```

## Tech Stack

- **LangGraph** — agent orchestration and conditional routing
- **LangChain + GPT-4o** — intent parsing and structured output
- **FastAPI** — webhook server
- **python-telegram-bot** — Telegram integration
- **Google Calendar API** — event creation and retrieval
- **Notion API** — task creation and retrieval
- **APScheduler** — daily summary cron job
- **Structlog** — structured JSON logging
- **Docker** — containerization

## Example Interactions

| Message | Intent | Action |
|---------|--------|--------|
| "Dentist appointment Thursday 3pm" | create_event | Creates Google Calendar event |
| "Buy groceries this week high priority" | create_task | Creates Notion task |
| "Call mom tomorrow" | create_task | Creates Notion task |
| "Team meeting Friday 10am" | create_event | Creates Google Calendar event |

## Getting Started

### 1. Clone the repo
```bash
git clone https://github.com/YOUR_USERNAME/personal-ai-agent.git
cd personal-ai-agent
```

### 2. Create virtual environment
```bash
python -m venv venv
source venv/bin/activate
```

### 3. Install dependencies
```bash
pip install -e ".[dev]"
```

### 4. Configure environment
```bash
cp .env.example .env
```

Fill in all values in `.env`:
- `OPENAI_API_KEY` — from platform.openai.com
- `TELEGRAM_BOT_TOKEN` — from @BotFather on Telegram
- `TELEGRAM_ALLOWED_USER_ID` — from @userinfobot on Telegram
- `NOTION_API_KEY` — from notion.so/my-integrations
- `NOTION_TASKS_DATABASE_ID` — from your Notion database URL

### 5. Authenticate Google Calendar
```bash
python -c "from app.tools.calendar import _get_calendar_service; _get_calendar_service()"
```

### 6. Run the server
```bash
uvicorn app.main:app --reload
```

### 7. Expose with ngrok
```bash
ngrok http 8000
```

### 8. Register Telegram webhook
```bash
curl -X POST "https://api.telegram.org/botYOUR_TOKEN/setWebhook" \
  -H "Content-Type: application/json" \
  -d '{"url": "https://YOUR_NGROK_URL/webhook/telegram"}'
```

## Project Structure
```
app/
├── config.py              # Settings and environment config
├── main.py                # FastAPI app + scheduler
├── agents/
│   ├── graph.py           # LangGraph graph definition and routing
│   ├── nodes.py           # Agent nodes (parse, create, respond)
│   └── state.py           # Typed agent state
├── tools/
│   ├── calendar.py        # Google Calendar integration
│   ├── notion.py          # Notion integration
│   └── telegram.py        # Telegram bot integration
├── routers/
│   └── webhook.py         # Telegram webhook endpoint
└── schemas/
    └── agent.py           # Pydantic models
```

## Daily Summary

Every morning at 8am the agent automatically sends a summary to Telegram:
```
🌅 Good morning! Here's your daily summary:

📅 Upcoming Events:
- Dentist Appointment — 2026-03-19T15:00:00+05:30

✅ Pending Tasks:
- [High] Buy groceries
```

## Running with Docker
```bash
docker-compose up --build
```