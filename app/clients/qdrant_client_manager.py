from qdrant_client import AsyncQdrantClient
from qdrant_client.grpc import Distance
from app.conf import QdrantConfig, app_config
import asyncio
from app.core import logger



class QdrantClientManager:


    def __init__(self, app_config: QdrantConfig):
        """
        初始化Qdrant客户端管理器
        :param app_config: Qdrant配置
        """
        self.config:QdrantConfig = app_config
        self.client: AsyncQdrantClient | None = None


    def init(self):
        """
        初始化Qdrant客户端
        :return: None
        """
        logger.info("初始化Qdrant客户端")
        self.client = AsyncQdrantClient(
            url=self.get_url(),
        )
        logger.info("Qdrant客户端初始化完成")

    async def close(self):
        """
        关闭Qdrant客户端
        :return: None
        """
        await self.client.close()
        logger.info("Qdrant客户端关闭完成")

    def get_url(self):
        """
        获取Qdrant客户端的URL
        :return: str
        """
        return f"http://{self.config.host}:{self.config.port}"

# Qdrant 全局客户端管理器
qdrant_client_manager = QdrantClientManager(app_config.qdrant)

if __name__ == '__main__':
    # 初始化Qdrant客户端
    qdrant_client_manager.init()

    from qdrant_client.grpc import VectorParams
    from qdrant_client.models import PointStruct
    async def test():
        # 2. 创建集合
        client = qdrant_client_manager.client
        await client.create_collection(
            collection_name="test",
            vectors_config=VectorParams(
                vector_size=1024,distance=Distance.Cosine
            ),
        )
        await client.upsert(
            collection_name="test",
            points=[
                PointStruct(id="1",vector=[0.5, 0.5, 0.5], payload={"id": "1","text": "这是一个测试向量"}),
                PointStruct(id="2",vector=[0.5, 0.5, 0.5], payload={"id": "2","text": "这是一个测试向量"})
            ]
    )
        
        # res = (await client.query_points(
        #     collection_name="test",
        #     vector=[0.5, 0.5, 0.5],
        #     limit=1,
        # )).points
        res = await client.query_points(
            collection_name="test",
            query=[0.5, 0.5, 0.5],
            with_payload=False,
            limit=1,
        )

        await qdrant_client_manager.close()
        print(res.points)
    asyncio.run(test())