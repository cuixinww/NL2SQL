from app.clients import embedding_client_manager
from app.clients import qdrant_client_manager
from app.clients import es_client_manager
from app.clients import meta_mysql_client_manager
from app.clients import dw_mysql_client_manager
from fastapi import FastAPI


async def lifespan(app: FastAPI):
    """
    应用生命周期管理
    """
    # 初始化客户端
    qdrant_client_manager.init()
    embedding_client_manager.init()
    es_client_manager.init()
    meta_mysql_client_manager.init()
    dw_mysql_client_manager.init()
    yield
    # 关闭客户端
    await qdrant_client_manager.close()
    await es_client_manager.close()
    await meta_mysql_client_manager.close()
    await dw_mysql_client_manager.close()
