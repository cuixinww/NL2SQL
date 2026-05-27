from dataclasses import dataclass


@dataclass
class TableRelation:
    id: str
    left_table_id: str
    left_cols: list[str]
    right_table_id: str
    right_cols: list[str]
    join_condition: str
    is_preferred: int
    description: str
