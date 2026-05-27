import asyncio
import sys
from pathlib import Path
from app.core.context import request_id_context_var

from loguru import logger


# 配置日志格式
log_format = (
    "<green>{time:YYYY-MM-DD HH:mm:ss.SSS}</green> | "
    "<level>{level: <8}</level> | "
    "<yellow>{extra[request_id]}</yellow> | "
    "<cyan>{name}</cyan>:<cyan>{function}</cyan>:<cyan>{line}</cyan> - "
    "<level>{message}</level>"
)

# 移除默认的日志记录器
logger.remove()
# 注入request_id到日志记录中
def inject_request_id(record):
    try:
        request_id = request_id_context_var.get()
        record["extra"]["request_id"] = request_id
    except LookupError:
        pass
    
 # 给日志打补丁，使其支持注入request_id
logger = logger.patch(inject_request_id)    
def setup_logger():
    from app.conf import app_config
    if app_config.logging.console.enable:
        logger.add(sink=sys.stdout, level=app_config.logging.console.level, format=log_format)
    if app_config.logging.file.enable:
        path = Path(app_config.logging.file.path)
        path.mkdir(parents=True, exist_ok=True)
        logger.add(
            sink=path / "app.log",
            level=app_config.logging.file.level,
            format=log_format,
            rotation=app_config.logging.file.rotation,
            retention=app_config.logging.file.retention,
            encoding="utf-8"
        )

setup_logger()


if __name__ == '__main__':
    async def graph(request: str):
        logger.info(request)

    async def main():
        await asyncio.gather(graph("test1"), graph("test2"))

    asyncio.run(main())