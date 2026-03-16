import structlog
from telegram import Bot
from telegram.constants import ParseMode
from app.config import get_settings

logger = structlog.get_logger()
settings = get_settings()

bot = Bot(token=settings.telegram_bot_token)


async def send_message(user_id: int, message: str) -> bool:
    log = logger.bind(user_id=user_id)
    try:
        await bot.send_message(
            chat_id=user_id,
            text=message,
            parse_mode=ParseMode.MARKDOWN,
        )
        log.info("telegram_message_sent")
        return True
    except Exception as e:
        log.error("telegram_message_failed", error=str(e))
        return False


async def send_daily_summary(user_id: int, events: list[dict], tasks: list[dict]) -> bool:
    try:
        events_text = ""
        if events:
            events_text = "\n*📅 Upcoming Events:*\n"
            for e in events:
                events_text += f"• {e['title']} — {e['start']}\n"
        else:
            events_text = "\n*📅 Upcoming Events:*\nNo upcoming events\n"

        tasks_text = ""
        if tasks:
            tasks_text = "\n*✅ Pending Tasks:*\n"
            for t in tasks:
                due = f" — due {t['due_date']}" if t['due_date'] else ""
                tasks_text += f"• [{t['priority']}] {t['title']}{due}\n"
        else:
            tasks_text = "\n*✅ Pending Tasks:*\nNo pending tasks\n"

        message = (
            f"*🌅 Good morning! Here's your daily summary:*\n"
            f"{events_text}"
            f"{tasks_text}"
        )

        return await send_message(user_id, message)

    except Exception as e:
        logger.error("daily_summary_failed", error=str(e))
        return False