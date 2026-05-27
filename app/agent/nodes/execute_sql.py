from app.agent.context import ContextSchema
from app.agent.state import DataAgentState
from langgraph.runtime import Runtime
from app.core import logger


async def execute_sql(state: DataAgentState, runtime: Runtime[ContextSchema]):
    logger.info("开始执行SQL")
    writer = runtime.stream_writer
    writer({"type": "progress", "step": "执行SQL", "status": "running"})
    try:
      sql = state["sql"]
      # 执行SQL语句
      result = await runtime.context.dw_mysql_repository.execute_sql(sql)
      writer({"type": "progress", "step": "执行SQL", "status": "success"})
      writer({"type": "result", "data": result})
      logger.info(f"成功执行SQL,执行结果: {result}")
    except Exception as e:
      writer({"type": "progress", "step": "执行SQL", "status": "error"})
      logger.error(f"执行SQL失败: {e}")
      raise Exception(f"执行SQL失败: {e}")
    