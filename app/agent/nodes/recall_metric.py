from app.core import logger
from app.agent.context import ContextSchema
from app.agent.state import DataAgentState
from app.agent.llm import create_llm
from app.prompt import load_prompt
from app.entities import MetricInfo
from langgraph.runtime import Runtime
from langchain_core.prompts import PromptTemplate
from langchain_core.output_parsers import JsonOutputParser


async def recall_metric(state: DataAgentState, runtime: Runtime[ContextSchema]):
   logger.info("开始从Qdrant数据库中召回指标")
   writer = runtime.stream_writer
   writer({"type": "progress", "step": "召回指标", "status": "running"})
   try:
      # 从状态中获取查询
      query = state["query"]
      keywords = state["keywords"]
      # 根据关键词，从qdradn数据库中召回字段信息
      # 1 获取qdrant仓库
      metric_qdrant_repository = runtime.context.metric_qdrant_repository
      # 2 使用llm补充关键词
      llm = create_llm()
      # 2.1 创建提示词
      prompt_template = load_prompt("extend_keywords_for_metric_recall")
      prompt = PromptTemplate.from_template(template=prompt_template)
      # 2.2 创建执行链
      chain = prompt | llm | JsonOutputParser()
      llm_keywords = await chain.ainvoke(query)
      logger.info(f"成功补充指标关键词: {llm_keywords}")
      # 2.3 合并关键词，并去重
      keywords = list(set(list(keywords) + list(llm_keywords)))
      # 3 从qdrant中召回指标信息
      metric_maps: dict[str,MetricInfo] = {}
      for keyword in keywords:
         # 3.1 将关键词向量化
         embedding = await runtime.context.embedding_client.aembed_query(keyword)
         # 3.2 从qdrant中召回指标信息
         metric_infos: list[MetricInfo] = await metric_qdrant_repository.recall_metrics(embedding)
         # 3.3 去重
         for metric_info in metric_infos:
            if metric_info.id not in metric_maps:
               metric_maps[metric_info.id] = metric_info
      writer({"type": "progress", "step": "召回指标", "status": "success"})
      logger.info(f"成功从Qdrant数据库中召回{len(metric_maps)}个指标: {[metric_info.name for metric_info in list(metric_maps.values())]}")  
      return {"retrieved_metric_infos": list(metric_maps.values())}
   except Exception as e:
      writer({"type": "progress", "step": "召回指标", "status": "error"})
      logger.error(f"召回指标失败: {e}")
      raise Exception(f"召回指标失败: {e}")
       
