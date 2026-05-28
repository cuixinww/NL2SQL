from dataclasses import dataclass
from typing import Optional


@dataclass
class ColumnConfig:
    name: str
    role: str
    description: str
    alias: list[str]
    sync: bool
    ref_table_id: str = ""
    ref_column_id: str = ""


@dataclass
class TableConfig:
    name: str
    table_type: str
    db_schema: str
    description: str
    alias: list[str]
    columns: list[ColumnConfig]


@dataclass
class MetricConfig:
    name: str
    description: str
    relevant_columns: list[str]
    alias: list[str]
    formula: str = ""
    default_filter: str = ""


@dataclass
class TableRelationConfig:
    id: str
    left_table_id: str
    left_cols: list[str]
    right_table_id: str
    right_cols: list[str]
    join_condition: str
    is_preferred: int = 0
    description: str = ""


@dataclass
class MetaConfig:
    tables: Optional[list[TableConfig]] = None
    metrics: Optional[list[MetricConfig]] = None
    table_relations: Optional[list[TableRelationConfig]] = None
