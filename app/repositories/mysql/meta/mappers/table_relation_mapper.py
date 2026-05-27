from dataclasses import asdict

from app.entities.table_relation import TableRelation
from app.models import TableRelationMySQL


class TableRelationMapper:
    @staticmethod
    def to_entity(model: TableRelationMySQL) -> TableRelation:
        return TableRelation(
            id=model.id,
            left_table_id=model.left_table_id,
            left_cols=model.left_cols,
            right_table_id=model.right_table_id,
            right_cols=model.right_cols,
            join_condition=model.join_condition,
            is_preferred=model.is_preferred,
            description=model.description
        )

    @staticmethod
    def to_model(entity: TableRelation) -> TableRelationMySQL:
        return TableRelationMySQL(**asdict(entity))
