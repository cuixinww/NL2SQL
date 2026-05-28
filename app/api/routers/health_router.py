from fastapi import APIRouter
from app.clients import meta_mysql_client_manager, dw_mysql_client_manager, qdrant_client_manager, es_client_manager
from sqlalchemy import text

health_router = APIRouter()


@health_router.get("/health")
async def health_check():
    checks = {}

    # MySQL meta
    try:
        async with meta_mysql_client_manager.session_factory() as session:
            await session.execute(text("SELECT 1"))
        checks["mysql_meta"] = "ok"
    except Exception as e:
        checks["mysql_meta"] = f"error: {e}"

    # MySQL dw
    try:
        async with dw_mysql_client_manager.session_factory() as session:
            await session.execute(text("SELECT 1"))
        checks["mysql_dw"] = "ok"
    except Exception as e:
        checks["mysql_dw"] = f"error: {e}"

    # Qdrant
    try:
        await qdrant_client_manager.client.get_collections()
        checks["qdrant"] = "ok"
    except Exception as e:
        checks["qdrant"] = f"error: {e}"

    # Elasticsearch
    try:
        await es_client_manager.es_client.ping()
        checks["elasticsearch"] = "ok"
    except Exception as e:
        checks["elasticsearch"] = f"error: {e}"

    all_ok = all(v == "ok" for v in checks.values())
    return {"status": "healthy" if all_ok else "degraded", "checks": checks}
