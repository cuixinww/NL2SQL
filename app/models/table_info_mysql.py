from sqlalchemy import String, Text
from sqlalchemy.types import JSON
from sqlalchemy.orm import Mapped, mapped_column

from app.models.base import Base


class TableInfoMySQL(Base):
    __tablename__ = "table_info"

    id: Mapped[str] = mapped_column(
        String(128),
        primary_key=True,
        comment="表编号"
    )
    name: Mapped[str | None] = mapped_column(
        String(128),
        comment="表名称"
    )
    table_type: Mapped[str | None] = mapped_column(
        String(32),
        comment="表类型(master/transaction/reference)"
    )
    db_schema: Mapped[str | None] = mapped_column(
        String(64),
        comment="所属数据库"
    )
    description: Mapped[str | None] = mapped_column(
        Text,
        comment="表描述"
    )
    alias: Mapped[dict | list | None] = mapped_column(
        JSON,
        comment="表别名"
    )
