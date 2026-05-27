from app.agent.context import ContextSchema
from app.agent.state import DataAgentState
from langgraph.runtime import Runtime
from datetime import datetime
from app.core import logger
from app.agent.state import DateInfoState, DBInfoState

async def add_extra_context(state: DataAgentState, runtime: Runtime[ContextSchema]):
   logger.info("开始添加额外上下文")
   writer = runtime.stream_writer
   writer({"type": "progress", "step": "添加额外上下文", "status": "running"})
   try:
      # 当前的时间信息
      today = datetime.today()
      # 日期
      date = today.strftime("%Y-%m-%d")
      # 星期
      weekday = today.strftime("%A")
      # 季度
      quarter = f"Q{(today.month - 1) // 3 + 1}"
      date_info = DateInfoState(date=date, weekday=weekday, quarter=quarter)
      db_info = await runtime.context.dw_mysql_repository.get_db_info()
      # 数据库信息
      db_info = DBInfoState(**db_info)
      writer({"type": "progress", "step": "添加额外上下文", "status": "success"})
      logger.info(f"额外上下文信息：数据库信息-{db_info} 日期信息-{date_info}")
      
      return {"date_info": date_info, "db_info": db_info}
   except Exception as e:
      writer({"type": "progress", "step": "添加额外上下文", "status": "error"})
      logger.error(f"添加额外上下文失败: {e}")
      raise Exception(f"添加额外上下文失败: {e}")
  
