
from elasticsearch import AsyncElasticsearch
from app.conf import ESConfig, app_config
from app.core import logger



class ESClientManager:

    def __init__(self, es_config: ESConfig ):
        """
        初始化ES客户端管理器
        :param es_config: ES配置
        """
        self.es_client: AsyncElasticsearch | None = None
        self.es_config: ESConfig = es_config

    def init(self):
        """
        初始化ES客户端
        :return: None
        """
        logger.info("初始化ES客户端")
        self.es_client = AsyncElasticsearch(
            hosts=[self._geturl()],
        )
        logger.info("ES客户端初始化完成")

    async def close(self):
        """
        关闭ES客户端
        :return: None
        """
        if self.es_client:
            await self.es_client.close()
            self.es_client = None
        logger.info("ES客户端关闭完成")

    def _geturl(self):
        """
        获取ES索引URL
        :return: str
        """
        return f"http://{self.es_config.host}:{self.es_config.port}"


# 初始化全局ES客户端管理器
es_client_manager = ESClientManager(app_config.es)

if __name__ == '__main__':
    es_client_manager.init()
    client = es_client_manager.es_client

    
    import asyncio


    async def test():
        await client.indices.create(index="test_index")
        await client.index(
            index="test_index",
            document={"text": "Hello, World!"}
        )
        res = await client.search(
            index="test_index"
        )
        print(res)
    
    asyncio.run(test())