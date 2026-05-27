from app.core import logger
from app.agent.context import ContextSchema
from app.agent.state import DataAgentState
from app.agent.llm import create_llm
from app.prompt import load_prompt
from app.entities import ColumnInfo
from langgraph.runtime import Runtime
from langchain_core.prompts import PromptTemplate
from langchain_core.output_parsers import StrOutputParser
import yaml


async def correct_sql(state: DataAgentState, runtime: Runtime[ContextSchema]):
   logger.info("开始校正SQL")
   writer = runtime.stream_writer
   writer({"type": "progress", "step": "校正SQL", "status": "running"})
   try:
      query = state["query"]
      sql = state["sql"]
      error = state["error"]
      suggestions = state["suggestions"]
      violations = state["violations"]
      table_infos = state["table_infos"]
      metric_infos = state["metric_infos"]
      date_info = state["date_info"]
      db_info = state["db_info"]
      # 生成SQL
      # 1 使用llm补充关键词
      llm = create_llm()
      # 1.1 创建提示词
      prompt_template = load_prompt("correct_sql")
      prompt = PromptTemplate.from_template(template=prompt_template)
      # 2.2 创建执行链
      chain = prompt | llm | StrOutputParser()
      llm_sql = await chain.ainvoke(
                           {
                           "query": query,
                           "sql": sql,
                           "error": error,
                           "suggestions": yaml.safe_dump(suggestions, allow_unicode=True, sort_keys=False),
                           "violations": yaml.safe_dump(violations, allow_unicode=True, sort_keys=False),
                           "table_infos": yaml.safe_dump(table_infos, allow_unicode=True, sort_keys=False),
                           "metric_infos": yaml.safe_dump(metric_infos, allow_unicode=True, sort_keys=False),
                           "date_info": yaml.safe_dump(date_info, allow_unicode=True, sort_keys=False),
                           "db_info": yaml.safe_dump(db_info, allow_unicode=True, sort_keys=False)
                           }
      )
      writer({"type": "progress", "step": "校正SQL", "status": "success"})
      logger.info(f"成功校正SQL: {llm_sql}")
      return {"sql": llm_sql}
   except Exception as e:
      writer({"type": "progress", "step": "校正SQL", "status": "error"})
      logger.error(f"校正SQL失败: {e}")
      raise Exception(f"校正SQL失败: {e}")
