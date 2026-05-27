from dataclasses import dataclass


@dataclass
class TableInfo:
    id: str
    name: str
    table_type: str
    db_schema: str
    description: str
    alias: list[str]
