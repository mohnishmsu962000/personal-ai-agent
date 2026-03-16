import structlog
from fastapi import APIRouter, Request, HTTPException
from telegram import Update
from telegram.ext import Application

from app.config import get_settings
from app.agents.graph import run_agent

logger = structlog.get_logger()
settings = get_settings()

router = APIRouter(prefix="/webhook", tags=["webhook"])

# Build telegram application
telegram_app = Application.builder().token(settings.telegram_bot_token).build()


@router.post("/telegram")
async def telegram_webhook(request: Request):
    """Receive updates from Telegram and run the agent."""
    try:
        data = await request.json()
        update = Update.de_json(data, telegram_app.bot)

        # Only handle messages
        if not update.message or not update.message.text:
            return {"status": "ignored"}

        user_id = update.message.from_user.id

        # Security — only allow configured user
        if user_id != settings.telegram_allowed_user_id:
            logger.warning("unauthorized_user", user_id=user_id)
            return {"status": "unauthorized"}

        message = update.message.text
        logger.info("message_received", user_id=user_id, message=message)

        # Run the agent
        result = await run_agent(message=message, user_id=user_id)

        return {
            "status": "ok",
            "intent": result.get("intent"),
            "success": result.get("success"),
        }

    except Exception as e:
        logger.error("webhook_failed", error=str(e))
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/health")
async def webhook_health():
    return {"status": "ok"}