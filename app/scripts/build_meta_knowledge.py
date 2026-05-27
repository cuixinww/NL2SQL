# import sys
from pathlib import Path
# sys.path.insert(0, str(Path(__file__).parents[2]))
import asyncio
from app.core import logger
from app.repositories.mysql.meta import MetaMySQLRepository
from app.repositories.mysql.dw import DWMySQLRepository
from app.repositories.qdrant import ColumnQdrantRepository
from app.repositories.es import ValueESRepository
from app.repositories.qdrant import MetricQdrantRepository
from app.services import MetaKnowledgeService

from app.clients import (
    meta_mysql_client_manager, 
    dw_mysql_client_manager, 
    qdrant_client_manager, 
    embedding_client_manager, 
    es_client_manager

)


async def build_meta_knowledge(config_path: Path):
    """
    构建元知识库
    :param config_path: 配置文件路径
    :return: None
    """
    # 构建元知识库
    logger.info("开始构建元知识库")
    meta_mysql_client_manager.init()  # 初始化元数据MySQL客户端
    dw_mysql_client_manager.init()  # 初始化数据仓库MySQL客户端
    qdrant_client_manager.init()  # 初始化Qdrant客户端
    embedding_client_manager.init()  # 初始化Embedding客户端
    es_client_manager.init()  # 初始化Elasticsearch客户端

   
    async with (meta_mysql_client_manager.session_factory() as meta_Session ,
                dw_mysql_client_manager.session_factory() as dw_session):
        meta_mysql_repository = MetaMySQLRepository(meta_Session)  # 初始化元数据库MySQL仓库
        dw_mysql_repository = DWMySQLRepository(dw_session)  # 初始化数据仓库MySQL仓库
        column_qdrant_repository = ColumnQdrantRepository(qdrant_client_manager.client)  # 初始化字段Qdrant仓库
        embedding_client = embedding_client_manager.client  # 初始化Embedding客户端
        value_es_repository = ValueESRepository(es_client_manager.es_client)  # 初始化值Elasticsearch客户端
        metric_qdrant_repository = MetricQdrantRepository(qdrant_client_manager.client)  # 初始化指标Qdrant仓库
        
        # 初始化元知识库服务
        meta_knowledge_service = MetaKnowledgeService(meta_mysql_repository, 
                                                        dw_mysql_repository,
                                                        column_qdrant_repository,
                                                        embedding_client,
                                                        value_es_repository,
                                                        metric_qdrant_repository,
                                                        )
        await meta_knowledge_service.build_meta_knowledge(config_path)

    await meta_mysql_client_manager.close()
    await dw_mysql_client_manager.close()
    await qdrant_client_manager.close()
    await es_client_manager.close()













if __name__ == "__main__":
    from argparse import ArgumentParser
    parser = ArgumentParser()

    parser.add_argument("-c", "--conf")  # option that takes a value

    args = parser.parse_args()

    config_path = Path(args.conf)


    asyncio.run(build_meta_knowledge(config_path))