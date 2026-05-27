from sqlalchemy import String, Text, Integer
from sqlalchemy.types import JSON
from sqlalchemy.orm import Mapped, mapped_column

from app.models.base import Base


class TableRelationMySQL(Base):
    __tablename__ = "table_relation"

    id: Mapped[str] = mapped_column(
        String(64),
        primary_key=True,
        comment="关系编号"
    )
    left_table_id: Mapped[str | None] = mapped_column(
        String(128),
        comment="左表编号"
    )
    left_cols: Mapped[dict | list | None] = mapped_column(
        JSON,
        comment="左表关联字段列表"
    )
    right_table_id: Mapped[str | None] = mapped_column(
        String(128),
        comment="右表编号"
    )
    right_cols: Mapped[dict | list | None] = mapped_column(
        JSON,
        comment="右表关联字段列表"
    )
    join_condition: Mapped[str | None] = mapped_column(
        String(512),
        comment="完整 ON 条件"
    )
    is_preferred: Mapped[int | None] = mapped_column(
        Integer,
        comment="是否为推荐路径"
    )
    description: Mapped[str | None] = mapped_column(
        Text,
        comment="关系说明"
    )
