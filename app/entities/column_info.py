from dataclasses import dataclass
from typing import Any


@dataclass
class ColumnInfo:
    id: str
    name: str
    data_type: str
    role: str
    examples: list[Any]
    description: str
    alias: list[str]
    table_id: str
    ref_table_id: str
    ref_column_id: str
