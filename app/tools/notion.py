import structlog
from notion_client import AsyncClient
from app.config import get_settings
from app.schemas.agent import NotionTask

logger = structlog.get_logger()
settings = get_settings()

client = AsyncClient(auth=settings.notion_api_key)


async def create_task(task: NotionTask) -> dict:
    log = logger.bind(title=task.title, priority=task.priority)

    try:
        properties = {
            "Name": {
                "title": [
                    {
                        "text": {
                            "content": task.title
                        }
                    }
                ]
            },
            "Status": {
                "select": {
                    "name": "To Do"
                }
            },
            "Priority": {
                "select": {
                    "name": task.priority
                }
            },
            "Source": {
                "select": {
                    "name": task.source
                }
            },
        }

        if task.due_date:
            properties["Due Date"] = {
                "date": {
                    "start": task.due_date
                }
            }

        result = await client.pages.create(
            parent={"database_id": settings.notion_tasks_database_id},
            properties=properties,
        )

        log.info("notion_task_created", page_id=result.get("id"))

        return {
            "success": True,
            "page_id": result.get("id"),
            "url": result.get("url"),
            "title": task.title,
            "priority": task.priority,
        }

    except Exception as e:
        log.error("notion_task_failed", error=str(e))
        return {"success": False, "error": str(e)}


async def get_pending_tasks() -> list[dict]:
    try:
        result = await client.databases.query(
            database_id=settings.notion_tasks_database_id,
            filter={
                "property": "Status",
                "select": {
                    "does_not_equal": "Done"
                }
            }
        )

        tasks = []
        for page in result.get("results", []):
            props = page.get("properties", {})
            title = props.get("Name", {}).get("title", [{}])
            title_text = title[0].get("text", {}).get("content", "No title") if title else "No title"
            status = props.get("Status", {}).get("select", {}).get("name", "Unknown")
            priority = props.get("Priority", {}).get("select", {}).get("name", "Medium")
            due_date = props.get("Due Date", {}).get("date", {})
            due = due_date.get("start") if due_date else None

            tasks.append({
                "title": title_text,
                "status": status,
                "priority": priority,
                "due_date": due,
                "url": page.get("url"),
            })

        return tasks

    except Exception as e:
        logger.error("get_tasks_failed", error=str(e))
        return []