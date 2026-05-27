from dataclasses import asdict

from app.entities.column_info import ColumnInfo
from app.models import ColumnInfoMySQL


class ColumnInfoMapper:
    @staticmethod
    def to_entity(column_info_mysql: ColumnInfoMySQL) -> ColumnInfo:
        return ColumnInfo(
            id=column_info_mysql.id,
            name=column_info_mysql.name,
            data_type=column_info_mysql.data_type,
            role=column_info_mysql.role,
            examples=column_info_mysql.examples,
            description=column_info_mysql.description,
            alias=column_info_mysql.alias,
            table_id=column_info_mysql.table_id,
            ref_table_id=column_info_mysql.ref_table_id,
            ref_column_id=column_info_mysql.ref_column_id
        )

    @staticmethod
    def to_model(column_info: ColumnInfo) -> ColumnInfoMySQL:
        return ColumnInfoMySQL(**asdict(column_info))
