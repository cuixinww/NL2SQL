from app.core import logger
from app.agent.context import ContextSchema
from app.agent.state import DataAgentState
from app.agent.graph import graph
from app.repositories.es import ValueESRepository
from app.repositories.mysql.meta import MetaMySQLRepository
from app.repositories.mysql.dw import DWMySQLRepository
from app.repositories.qdrant import ColumnQdrantRepository,MetricQdrantRepository
from app.clients.embedding_client_manager import EmbeddingClientManager
from langchain_openai import OpenAIEmbeddings
import json

class QueryService:
    
    def __init__(self,
            column_qdrant_repository: ColumnQdrantRepository,
            metric_qdrant_repository: MetricQdrantRepository,
            value_es_repository: ValueESRepository,
            meta_mysql_repository: MetaMySQLRepository,
            dw_mysql_repository: DWMySQLRepository,
            embedding_client: OpenAIEmbeddings):
        """
        初始化查询服务
        """
        self.embedding_client = embedding_client # 初始化embedding client
        self.column_qdrant_repository = column_qdrant_repository # 初始化column qdrant repository
        self.metric_qdrant_repository = metric_qdrant_repository # 初始化metric qdrant repository
        self.value_es_repository = value_es_repository # 初始化value es repository
        self.meta_mysql_repository = meta_mysql_repository # 初始化meta mysql repository
        self.dw_mysql_repository = dw_mysql_repository # 初始化dw mysql repository



    async def query(self, query: str):
        """
        执行查询
        """
        logger.info(f"开始查询: {query}")
        input = DataAgentState(query=query)

        content = ContextSchema(
                column_qdrant_repository=self.column_qdrant_repository,
                metric_qdrant_repository=self.metric_qdrant_repository,
                value_es_repository=self.value_es_repository,
                embedding_client=self.embedding_client,
                meta_repository=self.meta_mysql_repository,
                dw_mysql_repository=self.dw_mysql_repository
                )
        # 执行查询图
        try:
            
            async for chunk in graph.astream(input=input,context=content,stream_mode="custom"):
                yield f"data: {json.dumps(chunk, ensure_ascii=False, default=str)} \n\n"
        except Exception as e:
            yield f"data: {json.dumps({"type":"error","message":str(e)}, ensure_ascii=False, default=str)} \n\n"

       
