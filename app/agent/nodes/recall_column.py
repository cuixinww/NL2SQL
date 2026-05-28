import asyncio
from app.core import logger
from app.agent.context import ContextSchema
from app.agent.state import DataAgentState
from app.agent.llm import create_llm
from app.prompt import load_prompt
from app.entities import ColumnInfo
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


async def recall_column(state: DataAgentState, runtime: Runtime[ContextSchema]):
   logger.info("开始从Qdrant数据库中召回字段信息")
   writer = runtime.stream_writer
   writer({"type": "progress", "step": "召回字段", "status": "running"})
   try:
      keywords = state["keywords"]
      query = state["query"]
      column_qdrant_repository = runtime.context.column_qdrant_repository
      llm = create_llm()
      prompt_template = load_prompt("extend_keywords_for_column_recall")
      prompt = PromptTemplate.from_template(template=prompt_template)
      chain = prompt | llm | JsonOutputParser()
      llm_keywords = await chain.ainvoke(query)
      logger.info(f"成功补充关键词: {llm_keywords}")
      keywords = list(set(list(keywords) + list(llm_keywords)))
      column_maps: dict[str, ColumnInfo] = {}
      for keyword in keywords:
         embedding = await _embed_with_retry(runtime.context.embedding_client, keyword)
         column_infos: list[ColumnInfo] = await column_qdrant_repository.recall_columns(embedding)
         for column_info in column_infos:
            if column_info.id not in column_maps:
               column_maps[column_info.id] = column_info
      writer({"type": "progress", "step": "召回字段", "status": "success"})
      logger.info(f"成功从Qdrant数据库中召回{len(column_maps)}个字段信息: {[c.name for c in column_maps.values()]}")
      return {"retrieved_column_infos": list(column_maps.values())}
   except Exception as e:
      writer({"type": "progress", "step": "召回字段", "status": "error"})
      logger.error(f"召回字段信息失败: {e}")
      raise Exception(f"召回字段信息失败: {e}")
