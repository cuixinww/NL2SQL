from app.agent.context import ContextSchema
from app.core import logger
from app.agent.context import ContextSchema
from app.agent.state import DataAgentState
from app.agent.llm import create_llm
from app.prompt import load_prompt
from langgraph.runtime import Runtime
from langchain_core.prompts import PromptTemplate
from langchain_core.output_parsers import JsonOutputParser
from app.agent.state import MetricInfoState
import yaml

async def filter_metric(state: DataAgentState, runtime: Runtime[ContextSchema]):
   logger.info("开始过滤指标信息")
   writer = runtime.stream_writer
   writer({"type": "progress", "step": "过滤指标信息", "status": "running"})
   try:
      query = state["query"]
      metric_infos: list[MetricInfoState] = state["metric_infos"]
      # 1 使用llm补充关键词
      llm = create_llm()
      # 1.1 创建提示词
      prompt_template = load_prompt("filter_metric_info")
      prompt = PromptTemplate.from_template(template=prompt_template)
      # 1.2 创建执行链
      chain = prompt | llm | JsonOutputParser()

      result = await chain.ainvoke({"query": query, 
               "metric_infos": yaml.safe_dump(metric_infos, allow_unicode=True, sort_keys=False)})
      
      # 2 过滤后指标信息
      filter_metric_infos: list[MetricInfoState] = [ metric_info for metric_info in metric_infos if metric_info["name"] in result]
      
      writer({"type": "progress", "step": "过滤指标信息", "status": "success"})
      logger.info(f"成功过滤指标信息: {[metric_info['name'] for metric_info in filter_metric_infos]}")
      return {"metric_infos": filter_metric_infos}
   except Exception as e:
      writer({"type": "progress", "step": "过滤指标信息", "status": "error"})
      logger.error(f"过滤指标信息失败: {e}")
      raise Exception(f"过滤指标信息失败: {e}")
      
