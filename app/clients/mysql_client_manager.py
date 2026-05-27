# import sys
# from pathlib import Path
# sys.path.insert(0, str(Path(__file__).parents[2]))
from sqlalchemy.ext.asyncio.session import AsyncSession
from app.conf import DBConfig, app_config
from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncEngine, async_sessionmaker, create_async_engine
from typing import Optional
from app.core import logger

class MysqlClientManager:
    def __init__(self, mysql_config: DBConfig ):
        """
        初始化MySQL客户端管理器
        :param mysql_config: DB配置
        """
        self.mysql_config: DBConfig = mysql_config
        self.engine: Optional[AsyncEngine] = None
        self.session_factory = None
        
    def init(self):
        """
        初始化MySQL客户端
        :return: None
        """
        logger.info("初始化MySQL客户端")
        # 创建异步引擎
        self.engine = create_async_engine(
            self._get_url(),
            pool_size=10, # 连接池大小
            max_overflow=25,# 最大溢出连接数
            pool_timeout=30,# 连接池超时时间
            pool_pre_ping=True,# 连接池预检查
        )
        # 创建异步会话工厂
        self.session_factory = async_sessionmaker[AsyncSession](self.engine,
                                                  autoflush=True,# 自动刷新
                                                  expire_on_commit=False,# 提交后不过期
                                                  autobegin=True)# 自动会话开始
        logger.info("MySQL客户端初始化完成")
        
    async def close(self):
        """
        关闭MySQL客户端
        :return: None
        """
        if self.engine:
            await self.engine.dispose()
            self.engine = None
        logger.info("MySQL客户端关闭完成")

    def _get_url(self):
        """
        获取MySQL连接URL
        :return: MySQL连接URL
        """
        return f"mysql+asyncmy://{self.mysql_config.user}:{self.mysql_config.password}@{self.mysql_config.host}:{self.mysql_config.port}/{self.mysql_config.database}?charset=utf8mb4"


dw_mysql_client_manager = MysqlClientManager(app_config.db_dw)
meta_mysql_client_manager = MysqlClientManager(app_config.db_meta)

if __name__ == "__main__":

    import asyncio

    async def test():
        dw_mysql_client_manager.init()
        async with dw_mysql_client_manager.session_factory() as conn:
            sql = "select * from dw.dim_customer"
            result = await conn.execute(text(sql))
            print(type(result))
            # for row in result:
            #     print(row)
            print(result.fetchall())

    asyncio.run(test())