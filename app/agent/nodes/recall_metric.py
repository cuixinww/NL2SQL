import asyncio
from app.core import logger
from app.agent.context import ContextSchema
from app.agent.state import DataAgentState
from app.agent.llm import create_llm
from app.prompt import load_prompt
from app.entities import MetricInfo
from langgraph.runtime import Runtime
from langchain_core.prompts import PromptTemplate
from langchain_core.output_parsers import JsonOutputParser


async def _embed_with_retry(embedding_client, keyword: str, retries: int = 3):
   for attempt in range(retries):
      try:
         return await asyncio.wait_for(embedding_client.aembed_query(keyword), timeout=15)
      except Exception as e:
         if attempt == retries - 1:
            raise
         logger.warning(f"Embedding 调用失败({attempt+1}/{retries}): {e}, 重试中...")
         await asyncio.sleep(2)


async def recall_metric(state: DataAgentState, runtime: Runtime[ContextSchema]):
   logger.info("开始从Qdrant数据库中召回指标")
   writer = runtime.stream_writer
   writer({"type": "progress", "step": "召回指标", "status": "running"})
   try:
      query = state["query"]
      keywords = state["keywords"]
      metric_qdrant_repository = runtime.context.metric_qdrant_repository
      llm = create_llm()
      prompt_template = load_prompt("extend_keywords_for_metric_recall")
      prompt = PromptTemplate.from_template(template=prompt_template)
      chain = prompt | llm | JsonOutputParser()
      llm_keywords = await chain.ainvoke(query)
      logger.info(f"成功补充指标关键词: {llm_keywords}")
      keywords = list(set(list(keywords) + list(llm_keywords)))
      metric_maps: dict[str, MetricInfo] = {}
      for keyword in keywords:
         embedding = await _embed_with_retry(runtime.context.embedding_client, keyword)
         metric_infos: list[MetricInfo] = await metric_qdrant_repository.recall_metrics(embedding)
         for metric_info in metric_infos:
            if metric_info.id not in metric_maps:
               metric_maps[metric_info.id] = metric_info
      writer({"type": "progress", "step": "召回指标", "status": "success"})
      logger.info(f"成功从Qdrant数据库中召回{len(metric_maps)}个指标: {[m.name for m in metric_maps.values()]}")
      return {"retrieved_metric_infos": list(metric_maps.values())}
   except Exception as e:
      writer({"type": "progress", "step": "召回指标", "status": "error"})
      logger.error(f"召回指标失败: {e}")
      raise Exception(f"召回指标失败: {e}")
       
