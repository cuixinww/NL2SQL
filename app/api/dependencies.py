from app.services.query_service import QueryService
from app.clients.embedding_client_manager import EmbeddingClientManager
from app.repositories.qdrant import ColumnQdrantRepository
from app.repositories.qdrant import MetricQdrantRepository
from app.repositories.es import ValueESRepository
from app.repositories.mysql.meta import MetaMySQLRepository
from app.repositories.mysql.bank import BankMySQLRepository
from langchain_openai import OpenAIEmbeddings
from app.clients import embedding_client_manager
from app.clients import qdrant_client_manager
from app.clients import es_client_manager
from app.clients import meta_mysql_client_manager
from app.clients import bank_mysql_client_manager
from typing import Annotated
from fastapi import Depends
from sqlalchemy.ext.asyncio import AsyncSession



async def get_embedding_client_manager() -> OpenAIEmbeddings:
    """
    获取嵌入客户端管理器
    """
    return embedding_client_manager.client

async def get_column_qdrant_repository() -> ColumnQdrantRepository:
    """
    获取列Qdrant仓库
    """
    return ColumnQdrantRepository(qdrant_client_manager.client)

async def get_metric_qdrant_repository() -> MetricQdrantRepository:
    """
    获取指标Qdrant仓库
    """
    return MetricQdrantRepository(qdrant_client_manager.client)

async def get_value_es_repository() -> ValueESRepository:
    """
    获取值ES仓库
    """
    return ValueESRepository(es_client_manager.es_client)

async def get_meta_mysql_session():
    """
    获取元数据仓库异步会话
    """
    async with meta_mysql_client_manager.session_factory() as meta_Session:
        yield meta_Session
    
async def get_bank_mysql_session():
    """
    获取DW MySQL仓库异步会话
    """
    async with bank_mysql_client_manager.session_factory() as dw_Session:
        yield dw_Session
    
async def get_meta_mysql_repository(session: Annotated[AsyncSession, Depends(get_meta_mysql_session)]) -> MetaMySQLRepository:
    """
    获取元数据仓库
    """
    return MetaMySQLRepository(session)

async def get_bank_mysql_repository(session: Annotated[AsyncSession, Depends(get_bank_mysql_session)]) -> BankMySQLRepository:
    """
    获取DW MySQL仓库
    """
    return BankMySQLRepository(session)




async def get_query_service(
    embedding_client: Annotated[OpenAIEmbeddings, Depends(get_embedding_client_manager)],
    column_qdrant_repository: Annotated[ColumnQdrantRepository, Depends(get_column_qdrant_repository)],
    metric_qdrant_repository: Annotated[MetricQdrantRepository, Depends(get_metric_qdrant_repository)],
    value_es_repository: Annotated[ValueESRepository, Depends(get_value_es_repository)],
    meta_mysql_repository: Annotated[MetaMySQLRepository, Depends(get_meta_mysql_repository)],
    bank_mysql_repository: Annotated[BankMySQLRepository, Depends(get_bank_mysql_repository)],
) -> QueryService:
    """
    获取查询服务
    """
    return QueryService(embedding_client=embedding_client,
                        column_qdrant_repository=column_qdrant_repository,
                        metric_qdrant_repository=metric_qdrant_repository,
                        value_es_repository=value_es_repository,
                        meta_mysql_repository=meta_mysql_repository,
                        bank_mysql_repository=bank_mysql_repository)
        
