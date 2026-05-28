from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import text

# 禁止执行的 SQL 关键词（写操作 + DDL + 权限操作）
_BLOCKED_KEYWORDS = frozenset({
    "INSERT", "UPDATE", "DELETE", "DROP", "ALTER", "CREATE", "TRUNCATE",
    "GRANT", "REVOKE", "REPLACE", "RENAME", "CALL", "EXEC", "EXECUTE",
})

# 查询结果最大行数
MAX_ROWS = 1000

# 查询超时（秒）
QUERY_TIMEOUT_SECONDS = 30


class BankMySQLRepository:
    def __init__(self, session: AsyncSession):
        self.session = session

    def _check_sql_safe(self, sql: str):
        """校验 SQL 不含危险关键词"""
        first_token = sql.lstrip().split()[0].upper() if sql.strip() else ""
        if first_token in _BLOCKED_KEYWORDS:
            raise ValueError(f"禁止执行 {first_token} 类型的 SQL 语句")

    async def get_column_types(self, db_schema: str, table_name: str) -> dict[str, str]:
        query = f"SHOW COLUMNS FROM `{db_schema}`.`{table_name}`"
        result = await self.session.execute(text(query))
        result = result.mappings().fetchall()
        return {row['Field']: row['Type'] for row in result}

    async def get_column_values(self, db_schema: str, table_name: str, column_name: str, limit: int = 10) -> list:
        query = f"SELECT DISTINCT `{column_name}` FROM `{db_schema}`.`{table_name}` LIMIT :limit"
        result = await self.session.execute(text(query), {"limit": limit})
        return [row[0] for row in result.fetchall()]

    async def get_all_column_values(self, db_schema: str, table_name: str, column_name: str) -> list:
        query = f"SELECT DISTINCT `{column_name}` FROM `{db_schema}`.`{table_name}` LIMIT :limit"
        result = await self.session.execute(text(query), {"limit": MAX_ROWS})
        return [row[0] for row in result.fetchall()]

    async def get_db_info(self) -> dict:
        result = await self.session.execute(text("SELECT VERSION()"))
        version = result.scalar()
        dialect = self.session.bind.dialect.name
        if version:
            return {"version": version, "dialect": dialect}
        else:
            return None

    async def validate_sql(self, sql: str):
        self._check_sql_safe(sql)
        await self.session.execute(text(f"EXPLAIN {sql}"))

    async def execute_sql(self, sql: str) -> list[dict]:
        self._check_sql_safe(sql)
        # 注入行数限制：如果 SQL 没有 LIMIT，则追加
        limited_sql = sql.rstrip().rstrip(";")
        if "limit" not in limited_sql.lower():
            limited_sql = f"{limited_sql} LIMIT {MAX_ROWS}"
        # 设置查询超时
        await self.session.execute(text(f"SET SESSION MAX_EXECUTION_TIME={QUERY_TIMEOUT_SECONDS * 1000}"))
        result = await self.session.execute(text(limited_sql))
        return [dict(row) for row in result.mappings().fetchall()]
