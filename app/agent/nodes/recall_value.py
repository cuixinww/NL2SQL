import asyncio
from app.core import logger
from app.agent.context import ContextSchema
from app.agent.state import DataAgentState
from app.agent.llm import create_llm
from app.prompt import load_prompt
from app.entities import ValueInfo
from langgraph.runtime import Runtime
from langchain_core.prompts import PromptTemplate
from langchain_core.output_parsers import JsonOutputParser


async def recall_value(state: DataAgentState, runtime: Runtime[ContextSchema]):
   logger.info("开始从Elasticsearch中召回字段值")
   writer = runtime.stream_writer
   writer({"type": "progress", "step": "召回字段取值", "status": "running"})
   try:
      query = state["query"]
      keywords = state["keywords"]
      value_es_repository = runtime.context.value_es_repository
      llm = create_llm()
      prompt_template = load_prompt("extend_keywords_for_value_recall")
      prompt = PromptTemplate.from_template(template=prompt_template)
      chain = prompt | llm | JsonOutputParser()
      llm_keywords = await chain.ainvoke(query)
      logger.info(f"成功补充字段关键词: {llm_keywords}")
      keywords = list(set(list(keywords) + list(llm_keywords)))
      value_maps: dict[str, ValueInfo] = {}
      for keyword in keywords:
         for attempt in range(3):
            try:
               values: list[ValueInfo] = await asyncio.wait_for(
                  value_es_repository.recall_values(keyword), timeout=15
               )
               break
            except Exception as e:
               if attempt == 2:
                  raise
               logger.warning(f"ES 召回失败({attempt+1}/3): {e}, 重试中...")
               await asyncio.sleep(2)
         for value in values:
            if value.id not in value_maps:
               value_maps[value.id] = value
      writer({"type": "progress", "step": "召回字段取值", "status": "success"})
      logger.info(f"成功从Elasticsearch中召回{len(value_maps)}个字段值: {[v.value for v in value_maps.values()]}")
      return {"retrieved_values_infos": list(value_maps.values())}
   except Exception as e:
      writer({"type": "progress", "step": "召回字段取值", "status": "error"})
      logger.error(f"召回字段取值失败: {e}")
      raise Exception(f"召回字段取值失败: {e}")
