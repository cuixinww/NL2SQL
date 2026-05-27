from dataclasses import asdict

from app.entities.table_info import TableInfo
from app.models import TableInfoMySQL


class TableInfoMapper:
    @staticmethod
    def to_entity(table_info_mysql: TableInfoMySQL) -> TableInfo:
        return TableInfo(
            id=table_info_mysql.id,
            name=table_info_mysql.name,
            table_type=table_info_mysql.table_type,
            db_schema=table_info_mysql.db_schema,
            description=table_info_mysql.description,
            alias=table_info_mysql.alias
        )

    @staticmethod
    def to_model(table_info: TableInfo) -> TableInfoMySQL:
        return TableInfoMySQL(**asdict(table_info))
