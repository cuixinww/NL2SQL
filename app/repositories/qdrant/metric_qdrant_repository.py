from qdrant_client import AsyncQdrantClient
from app.conf import app_config
from qdrant_client.models import VectorParams, Distance,PointStruct
from app.entities import MetricInfo
from dataclasses import asdict

class MetricQdrantRepository:
    """
    指标Qdrant仓库
    """
    # 指标向量索引集合名称
    METRIC_COLLECTION_NAME = "metrics_info_collection"


    def __init__(self, qdrant_client: AsyncQdrantClient):
        self.qdrant_client = qdrant_client  # 初始化Qdrant客户端


    async def ensure_icollection(self):
        """
        创建指标向量索引
        :return: None 
        """
        # 检查索引是否存在
        if await self.qdrant_client.collection_exists(collection_name=self.METRIC_COLLECTION_NAME):
            # 索引存在，先删除
            await self.qdrant_client.delete_collection(collection_name=self.METRIC_COLLECTION_NAME)

        await self.qdrant_client.create_collection(
            collection_name=self.METRIC_COLLECTION_NAME,
            vectors_config=VectorParams(
                size=app_config.qdrant.embedding_size, # 向量维度
                distance=Distance.COSINE # 距离度量
            ),
        )

    async def upsert(self, ids: list[str], embeddings: list[list[float]], payloads: list[MetricInfo],batch_size: int = 20):
        """
        保存指标信息到Qdrant
        :param ids: 指标ID列表
        :param embeddings: 指标向量列表
        :param payloads: 指标信息列表
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
                collection_name=self.METRIC_COLLECTION_NAME,
                points=batch_points
            )

    async def recall_metrics(self, query: list[float],score_threshold: float = 0.6,limit: int = 10) -> list[MetricInfo]:
        """
        从Qdrant中召回指标信息
        :param query: 查询向量
        :param score_threshold: 筛选阈值
        :param limit: 返回结果数量
        :return: 指标信息列表
        """
        # 从Qdrant召回指标信息
        results = await self.qdrant_client.query_points(
            collection_name=self.METRIC_COLLECTION_NAME,
            query=query,
            limit=limit,
            score_threshold=score_threshold,
            with_payload=True,
        )
        # 提取指标信息
        metric_infos: list[MetricInfo] = [MetricInfo(**point.payload) for point in results.points]
        return metric_infos
