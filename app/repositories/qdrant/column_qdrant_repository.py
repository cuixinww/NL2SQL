from re import X
from qdrant_client import AsyncQdrantClient
from app.entities import ColumnInfo
from qdrant_client.models import VectorParams, Distance,PointStruct
from dataclasses import asdict
from app.conf import app_config
class ColumnQdrantRepository:
    """
    字段Qdrant仓库
    """
    # 字段向量索引集合名称
    COLUMN_COLLECTION_NAME = "column_info_collection"


    def __init__(self, qdrant_client: AsyncQdrantClient):
        self.qdrant_client = qdrant_client

    async def ensure_icollection(self):
        """
        创建字段向量索引
        :return: None 
        """
        # 检查索引是否存在
        if await self.qdrant_client.collection_exists(collection_name=self.COLUMN_COLLECTION_NAME):
            # 索引存在，先删除
            await self.qdrant_client.delete_collection(collection_name=self.COLUMN_COLLECTION_NAME)

        await self.qdrant_client.create_collection(
            collection_name=self.COLUMN_COLLECTION_NAME,
            vectors_config=VectorParams(
                size=app_config.qdrant.embedding_size, # 向量维度
                distance=Distance.COSINE # 距离度量
                ),
        )    


    async def upsert(self, ids: list[str], embeddings: list[list[float]], payloads: list[ColumnInfo],batch_size: int = 20):
        """
        保存字段信息到Qdrant
        :param ids: 字段ID列表
        :param embeddings: 字段向量列表
        :param payloads: 字段信息列表
        :return: None
        """
        # 合并id、向量和payload
        zipped = list(zip(ids, embeddings, payloads))
        # 分批次处理
        for i in range(0, len(zipped), batch_size):
            batch = zipped[i:i + batch_size]
            # 转换为PointStruct列表
            batch_points: list[PointStruct] = [PointStruct(id=id, vector=embedding, payload=asdict(payload)) 
                            for id, embedding, payload in batch]
            # 保存数据到Qdrant
            await self.qdrant_client.upsert(
                collection_name=self.COLUMN_COLLECTION_NAME,
                points=batch_points
            )

    async def recall_columns(self, query: list[float],score_threshold: float = 0.6,limit: int = 10) -> list[ColumnInfo]:
        """
        从Qdrant中召回字段信息
        :param query: 查询向量
        :return: 字段信息列表
        """
        response = await self.qdrant_client.query_points(
            collection_name=self.COLUMN_COLLECTION_NAME,
            query=query,
            with_payload=True,
            score_threshold=score_threshold,
            limit=limit
        )
        if not response.points:
            return []

        column_infos: list[ColumnInfo] = [ ColumnInfo(**point.payload) for point in response.points ]

        return column_infos

             