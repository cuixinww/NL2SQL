import signal
import asyncio
from app.clients import embedding_client_manager
from app.clients import qdrant_client_manager
from app.clients import es_client_manager
from app.clients import meta_mysql_client_manager
from app.clients import dw_mysql_client_manager
from fastapi import FastAPI


async def lifespan(app: FastAPI):
    # 初始化客户端
    qdrant_client_manager.init()
    embedding_client_manager.init()
    es_client_manager.init()
    meta_mysql_client_manager.init()
    dw_mysql_client_manager.init()

    # 注册优雅停机：收到 SIGTERM/SIGINT 后等待在途请求完成
    shutdown_event = asyncio.Event()

    def _signal_handler():
        shutdown_event.set()

    loop = asyncio.get_running_loop()
    for sig in (signal.SIGTERM, signal.SIGINT):
        try:
            loop.add_signal_handler(sig, _signal_handler)
        except NotImplementedError:
            # Windows 不支持 add_signal_handler
            pass

    yield

    # 关闭客户端
    await qdrant_client_manager.close()
    await es_client_manager.close()
    await meta_mysql_client_manager.close()
    await dw_mysql_client_manager.close()
