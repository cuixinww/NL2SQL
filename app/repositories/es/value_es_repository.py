from elasticsearch import AsyncElasticsearch
from app.entities import ValueInfo
from dataclasses import asdict

class ValueESRepository:
    """
    值Elasticsearch仓库
    """
    INDEX_NAME = "value_index"
    INDEX_MAPPINGS = {
        "dynamic": False,
        "properties": {
            "id": {"type": "keyword"},# 值的唯一标识
            "value": {"type": "text", "analyzer": "ik_max_word", "search_analyzer": "ik_max_word"},# 值的文本内容
            "column_id": {"type": "keyword"}# 字段所属的字段标识
        }
    }
    def __init__(self, es_client: AsyncElasticsearch):
        self.es_client = es_client


    async def ensure_index(self):
        """
        确保Elasticsearch索引存在
        :return: None
        """
        # 检查索引是否存在
        indices = await self.es_client.indices.exists(index=self.INDEX_NAME)
        if  not indices:
            await self.es_client.indices.create(index=self.INDEX_NAME,mappings=self.INDEX_MAPPINGS)



    async def index(self, value_infos: list[ValueInfo], batch_size=20):
        """
        批量索引值到Elasticsearch
        :param value_infos: 值信息列表
        :param batch_size: 批量大小，默认20条
        :return: None
        """
        # 批量索引值到Elasticsearch
        for i in range(0, len(value_infos), batch_size):
            batch_value_infos = value_infos[i:i+batch_size]
           
            operations = []
            for value_info in batch_value_infos:
                operations.append({"index": {"_index": self.INDEX_NAME, "_id": value_info.id}})
                operations.append(asdict(value_info))
            # 批量索引到Elasticsearch
            await self.es_client.bulk(operations=operations)


    async def recall_values(self, keyword: str,score_threshold: float = 0.6,limit: int = 10) -> list[ValueInfo]:
        """
        根据关键词召回值
        :param keyword: 关键词
        :param score_threshold: 分数阈值，默认0.6
        :param limit: 返回数量限制，默认10
        :return: 值信息列表
        """
        # 根据关键词召回值
        response = await self.es_client.search(
            index=self.INDEX_NAME,
            query={"match": {"value": keyword}},
            size=limit,
            min_score=score_threshold
        )
        # 提取值信息
        values = [ ValueInfo(**hit["_source"]) for hit in response["hits"]["hits"]]
        return values