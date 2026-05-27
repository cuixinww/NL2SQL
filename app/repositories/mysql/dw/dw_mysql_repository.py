from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import text


class DWMySQLRepository:
    """
    数据仓库MySQL仓库
    """
    def __init__(self, session: AsyncSession):
        self.session = session

    async def get_column_types(self, db_schema: str, table_name: str) -> dict[str, str]:
        """
        获取指定表的所有字段类型
        """
        query = f"SHOW COLUMNS FROM `{db_schema}`.`{table_name}`"
        result = await self.session.execute(text(query))
        result = result.mappings().fetchall()
        column_types = {row['Field']: row['Type'] for row in result}
        return column_types

    async def get_column_values(self, db_schema: str, table_name: str, column_name: str, limit: int = 10) -> list:
        """
        获取指定表指定字段的部分取值
        """
        query = f"SELECT DISTINCT `{column_name}` FROM `{db_schema}`.`{table_name}` LIMIT :limit"
        result = await self.session.execute(text(query), {"limit": limit})
        result = result.fetchall()
        column_values = [row[0] for row in result]
        return column_values

    async def get_all_column_values(self, db_schema: str, table_name: str, column_name: str) -> list:
        """
        获取指定表指定字段的所有取值
        """
        query = f"SELECT DISTINCT `{column_name}` FROM `{db_schema}`.`{table_name}`"
        result = await self.session.execute(text(query))
        result = result.fetchall()
        column_values = [row[0] for row in result]
        return column_values

    async def get_db_info(self) -> dict:
        """
        获取数据库信息
        """
        result = await self.session.execute(text("SELECT VERSION()"))
        version = result.scalar()
        dialect = self.session.bind.dialect.name
        if version:
            return {"version": version, "dialect": dialect}
        else:
            return None

    async def validate_sql(self, sql: str) -> str:
        """
        验证SQL语句是否符合语法
        """
        await self.session.execute(text("EXPLAIN " + sql))

    async def execute_sql(self, sql: str) -> list[dict]:
        """
        执行SQL语句
        """
        result = await self.session.execute(text(sql))
        return [dict(row) for row in result.mappings().fetchall()]
