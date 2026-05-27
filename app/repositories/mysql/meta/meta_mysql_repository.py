from sqlalchemy.ext.asyncio import AsyncSession
from app.repositories.mysql.meta.mappers import TableInfoMapper, ColumnInfoMapper, MetricInfoMapper, TableRelationMapper
from app.entities import TableInfo, ColumnInfo, MetricInfo, TableRelation
from app.models import ColumnInfoMySQL, TableInfoMySQL, TableRelationMySQL
from sqlalchemy import text
from app.core import logger


class MetaMySQLRepository:
    """
    元数据库MySQL仓库
    """
    def __init__(self, session: AsyncSession):
        self.session = session

    def save_table_infos(self, table_infos: list[TableInfo]):
        """
        保存表信息到元数据数据库
        """
        models = [TableInfoMapper.to_model(table_info) for table_info in table_infos]
        self.session.add_all(models)

    def save_column_infos(self, column_infos: list[ColumnInfo]):
        """
        保存字段信息到元数据数据库
        """
        models = [ColumnInfoMapper.to_model(column_info) for column_info in column_infos]
        self.session.add_all(models)

    def save_metric_infos(self, metric_infos: list[MetricInfo]):
        """
        保存指标信息到元数据数据库
        """
        models = [MetricInfoMapper.to_model(metric_info) for metric_info in metric_infos]
        self.session.add_all(models)

    def save_table_relations(self, table_relations: list[TableRelation]):
        """
        保存表关系信息到元数据数据库
        """
        models = [TableRelationMapper.to_model(relation) for relation in table_relations]
        self.session.add_all(models)

    async def delete_all(self):
        """
        删除所有元数据信息
        """
        await self.session.execute(text("SET FOREIGN_KEY_CHECKS = 0"))
        await self.session.execute(text("TRUNCATE TABLE `table_relation`"))
        await self.session.execute(text("TRUNCATE TABLE `metric_info`"))
        await self.session.execute(text("TRUNCATE TABLE `column_info`"))
        await self.session.execute(text("TRUNCATE TABLE `table_info`"))
        await self.session.execute(text("SET FOREIGN_KEY_CHECKS = 1"))
        logger.info("元数据库MySQL数据库所有元数据信息已删除")

    async def get_column_info_by_id(self, column_id: str) -> ColumnInfo:
        """
        根据字段ID获取字段信息
        """
        result = await self.session.get(ColumnInfoMySQL, column_id)
        if result:
            return ColumnInfoMapper.to_entity(result)
        else:
            return None

    async def get_table_info_by_id(self, table_id: str) -> TableInfo:
        """
        根据表ID获取表信息
        """
        result = await self.session.get(TableInfoMySQL, table_id)
        if result:
            return TableInfoMapper.to_entity(result)
        else:
            return None

    async def get_primary_key_by_id(self, table_id: str) -> list[ColumnInfo]:
        """
        根据表ID获取主键和外键字段
        """
        sql = "SELECT * FROM column_info WHERE table_id = :table_id AND role in ('primary_key','foreign_key')"
        result = await self.session.execute(text(sql), {"table_id": table_id})
        column_infos = [ColumnInfo(**dict(row)) for row in result.mappings().fetchall()]
        if column_infos:
            return column_infos
        else:
            return None

    async def get_table_relations_by_tables(self, table_ids: list[str]) -> list[TableRelation]:
        """
        根据表ID列表查询关联关系
        """
        if not table_ids:
            return []
        placeholders = ", ".join([f":t{i}" for i in range(len(table_ids))])
        sql = f"SELECT * FROM table_relation WHERE left_table_id IN ({placeholders}) OR right_table_id IN ({placeholders})"
        params = {f"t{i}": tid for i, tid in enumerate(table_ids)}
        params.update({f"t{i}_r": tid for i, tid in enumerate(table_ids)})
        # 修正：需要两组参数
        sql = f"SELECT * FROM table_relation WHERE left_table_id IN ({placeholders}) OR right_table_id IN ({placeholders})"
        result = await self.session.execute(text(sql), {**{f"t{i}": tid for i, tid in enumerate(table_ids)},
                                                        **{f"t{i+len(table_ids)}": tid for i, tid in enumerate(table_ids)}})
        relations = [TableRelation(**dict(row)) for row in result.mappings().fetchall()]
        return relations
