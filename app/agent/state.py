from typing import TypedDict
from app.entities import ColumnInfo, MetricInfo, ValueInfo
from typing import Optional


class ColumnInfoState(TypedDict):
    name: str
    data_type: str
    role: str
    examples: list
    description: str
    alias: list[str]
    ref_table_id: str
    ref_column_id: str


class TableInfoState(TypedDict):
    name: str
    table_type: str
    db_schema: str
    description: str
    alias: list[str]
    columns: list[ColumnInfoState]


class MetricInfoState(TypedDict):
    name: str
    description: str
    relevant_columns: list[str]
    alias: list[str]
    formula: str
    default_filter: str


class DateInfoState(TypedDict):
    date: str
    weekday: str
    quarter: str


class DBInfoState(TypedDict):
    dialect: str
    version: str


class DataAgentState(TypedDict):
    query: str
    keywords: Optional[list[str]] = None
    retrieved_column_infos: Optional[list[ColumnInfo]] = None
    retrieved_metric_infos: Optional[list[MetricInfo]] = None
    retrieved_values_infos: Optional[list[ValueInfo]] = None
    table_infos: Optional[list[TableInfoState]] = None
    metric_infos: Optional[list[MetricInfoState]] = None
    date_info: Optional[DateInfoState] = None
    db_info: Optional[DBInfoState] = None
    error: Optional[str] = None
    violations: Optional[list[str]] = None
    suggestions: Optional[list[str]] = None
    sql: Optional[str] = None
    result: Optional[list[dict]] = None
    join_paths: Optional[list[str]] = None
    retry_count: Optional[int] = None
