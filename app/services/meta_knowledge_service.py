from app.core import logger
from app.conf import load_config
from app.conf.meta_config import MetaConfig
from app.repositories.mysql.meta import MetaMySQLRepository
from app.repositories.mysql.dw import DWMySQLRepository
from app.repositories.qdrant import ColumnQdrantRepository
from app.repositories.es import ValueESRepository
from app.repositories.qdrant import MetricQdrantRepository
from app.entities import ColumnInfo, TableInfo, ValueInfo, MetricInfo, TableRelation
from langchain_openai import OpenAIEmbeddings
from pathlib import Path
from decimal import Decimal
from datetime import date, datetime
import uuid


def _serialize_value(v):
    if isinstance(v, (date, datetime)):
        return v.isoformat()
    if isinstance(v, Decimal):
        return str(v)
    return v


class MetaKnowledgeService:
    """
    元知识库服务
    """
    def __init__(self,
                    meta_mysql_repository: MetaMySQLRepository,
                    dw_mysql_repository: DWMySQLRepository,
                    column_qdrant_repository: ColumnQdrantRepository,
                    embedding_client: OpenAIEmbeddings,
                    value_es_repository: ValueESRepository,
                    metric_qdrant_repository: MetricQdrantRepository
                ):
        self.meta_mysql_repository = meta_mysql_repository
        self.dw_mysql_repository = dw_mysql_repository
        self.column_qdrant_repository = column_qdrant_repository
        self.embedding_client = embedding_client
        self.value_es_repository = value_es_repository
        self.metric_qdrant_repository = metric_qdrant_repository

    async def _sync_tables(self, tables: list) -> list[ColumnInfo]:
        """
        同步表信息和字段信息到元数据MySQL数据库
        """
        logger.info("开始同步表信息和字段信息")
        table_infos: list[TableInfo] = []
        column_infos: list[ColumnInfo] = []
        for table in tables:
            table_info = TableInfo(
                id=f"{table.db_schema}.{table.name}",
                name=table.name,
                table_type=table.table_type,
                db_schema=table.db_schema,
                description=table.description,
                alias=table.alias
            )
            table_infos.append(table_info)

            # 查询该表的所有字段类型
            column_types: dict[str, str] = await self.dw_mysql_repository.get_column_types(table.db_schema, table.name)
            for column in table.columns:
                # 查询该字段的部分取值作为示例
                column_values: list = await self.dw_mysql_repository.get_column_values(table.db_schema, table.name, column.name, 10)
                column_values = [_serialize_value(v) for v in column_values]

                column_info = ColumnInfo(
                    id=f"{table.db_schema}.{table.name}.{column.name}",
                    name=column.name,
                    data_type=column_types[column.name],
                    role=column.role,
                    examples=column_values,
                    description=column.description,
                    alias=column.alias,
                    table_id=f"{table.db_schema}.{table.name}",
                    ref_table_id=column.ref_table_id,
                    ref_column_id=column.ref_column_id
                )
                column_infos.append(column_info)

        # 保存表信息和字段信息到元数据数据库
        async with self.meta_mysql_repository.session.begin():
            await self.meta_mysql_repository.delete_all()
            self.meta_mysql_repository.save_table_infos(table_infos)
            self.meta_mysql_repository.save_column_infos(column_infos)

        logger.info("表信息和字段信息同步完成")
        return column_infos

    async def _create_embedding_index(self, column_infos: list[ColumnInfo]):
        """
        对字段信息建立向量索引
        """
        logger.info("开始创建字段向量索引")
        await self.column_qdrant_repository.ensure_icollection()
        points: list[dict] = []
        for column in column_infos:
            points.append({
                "id": uuid.uuid4(),
                "embedding_text": column.name,
                "payload": column,
            })
            points.append({
                "id": uuid.uuid4(),
                "embedding_text": column.description,
                "payload": column,
            })
            for alia in column.alias:
                points.append({
                    "id": uuid.uuid4(),
                    "embedding_text": alia,
                    "payload": column,
                })
        embedding_texts = [point["embedding_text"] for point in points]
        embedding_batch_size = 10
        embeddings = []
        for i in range(0, len(embedding_texts), embedding_batch_size):
            batch_embedding_texts = embedding_texts[i:i+embedding_batch_size]
            batch_embeddings = await self.embedding_client.aembed_documents(batch_embedding_texts)
            embeddings.extend(batch_embeddings)
        ids = [point["id"] for point in points]
        payloads = [point["payload"] for point in points]
        await self.column_qdrant_repository.upsert(ids, embeddings, payloads)
        logger.info("字段向量索引创建完成")

    async def _create_es_index(self, meta_config: MetaConfig, column_infos: list[ColumnInfo]):
        """
        对指定的字段取值建立Elasticsearch全文索引
        """
        logger.info("开始创建值Elasticsearch索引")
        await self.value_es_repository.ensure_index()
        column2sync: dict[str, bool] = {}
        for table in meta_config.tables:
            for column in table.columns:
                column2sync[f"{table.db_schema}.{table.name}.{column.name}"] = column.sync
        value_infos: list[ValueInfo] = []
        for column_info in column_infos:
            if column2sync.get(column_info.id, False):
                table_name = column_info.table_id.split(".")[-1]
                column_name = column_info.name
                db_schema = column_info.table_id.split(".")[0]
                values = await self.dw_mysql_repository.get_all_column_values(
                    db_schema, table_name, column_name
                )
                values = [_serialize_value(v) for v in values]
                value_infos.extend([
                    ValueInfo(
                        id=f"{column_info.id}.{value}",
                        value=value,
                        column_id=column_info.id,
                    )
                    for value in values
                ])
        await self.value_es_repository.index(value_infos)
        logger.info("值Elasticsearch索引创建完成")

    async def _sync_metrics(self, metrics: list) -> list[MetricInfo]:
        """
        同步指标信息到元数据MySQL数据库
        """
        logger.info("开始同步指标信息")
        metric_infos: list[MetricInfo] = []
        for metric in metrics:
            metric_info = MetricInfo(
                id=metric.name,
                name=metric.name,
                description=metric.description,
                relevant_columns=metric.relevant_columns,
                alias=metric.alias,
                formula=metric.formula,
                default_filter=metric.default_filter
            )
            metric_infos.append(metric_info)

        async with self.meta_mysql_repository.session.begin():
            self.meta_mysql_repository.save_metric_infos(metric_infos)

        logger.info("指标信息同步完成")
        return metric_infos

    async def _sync_table_relations(self, table_relations: list) -> list[TableRelation]:
        """
        同步表关系信息到元数据MySQL数据库
        """
        logger.info("开始同步表关系信息")
        relations: list[TableRelation] = []
        for rel in table_relations:
            relation = TableRelation(
                id=rel.id,
                left_table_id=rel.left_table_id,
                left_cols=rel.left_cols,
                right_table_id=rel.right_table_id,
                right_cols=rel.right_cols,
                join_condition=rel.join_condition,
                is_preferred=rel.is_preferred,
                description=rel.description
            )
            relations.append(relation)

        async with self.meta_mysql_repository.session.begin():
            self.meta_mysql_repository.save_table_relations(relations)

        logger.info("表关系信息同步完成")
        return relations

    async def _create_metrics_embedding_index(self, metric_infos: list[MetricInfo]):
        """
        对指标信息建立向量索引
        """
        logger.info("开始建立指标信息向量索引")
        await self.metric_qdrant_repository.ensure_icollection()
        points: list[dict] = []
        for metric_info in metric_infos:
            points.append({
                "id": uuid.uuid4(),
                "embedding_text": metric_info.name,
                "payload": metric_info,
            })
            points.append({
                "id": uuid.uuid4(),
                "embedding_text": metric_info.description,
                "payload": metric_info,
            })
            for alia in metric_info.alias:
                points.append({
                    "id": uuid.uuid4(),
                    "embedding_text": alia,
                    "payload": metric_info,
                })
        embedding_texts = [point["embedding_text"] for point in points]
        embedding_batch_size = 10
        embeddings = []
        for i in range(0, len(embedding_texts), embedding_batch_size):
            batch_embedding_texts = embedding_texts[i:i+embedding_batch_size]
            batch_embeddings = await self.embedding_client.aembed_documents(batch_embedding_texts)
            embeddings.extend(batch_embeddings)
        ids = [point["id"] for point in points]
        payloads = [point["payload"] for point in points]
        await self.metric_qdrant_repository.upsert(ids, embeddings, payloads)
        logger.info("指标信息向量索引建立完成")
        return metric_infos

    async def build_meta_knowledge(self, config_path: Path):
        """
        构建元知识库
        """
        meta_config: MetaConfig = load_config(config_path, MetaConfig)

        # 同步表信息
        if meta_config.tables:
            logger.info("开始同步表信息")
            column_infos = await self._sync_tables(meta_config.tables)
            await self._create_embedding_index(column_infos)
            await self._create_es_index(meta_config, column_infos)
            logger.info("表信息同步完成")

        # 同步指标信息
        if meta_config.metrics:
            logger.info("开始同步指标信息")
            metric_infos = await self._sync_metrics(meta_config.metrics)
            await self._create_metrics_embedding_index(metric_infos)
            logger.info("指标信息同步完成")

        # 同步表关系信息
        if meta_config.table_relations:
            logger.info("开始同步表关系信息")
            await self._sync_table_relations(meta_config.table_relations)
            logger.info("表关系信息同步完成")
