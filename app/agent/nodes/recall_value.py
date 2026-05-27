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
      # 从状态中获取查询
      query = state["query"]
      keywords = state["keywords"]
      # 根据关键词，从qdradn数据库中召回字段信息
      # 1 获取qdrant仓库
      value_es_repository = runtime.context.value_es_repository
      # 2 使用llm补充关键词
      llm = create_llm()
      # 2.1 创建提示词
      prompt_template = load_prompt("extend_keywords_for_value_recall")
      prompt = PromptTemplate.from_template(template=prompt_template)
      # 2.2 创建执行链
      chain = prompt | llm | JsonOutputParser()
      llm_keywords = await chain.ainvoke(query)
      logger.info(f"成功补充字段关键词: {llm_keywords}")
      # 2.3 合并关键词，并去重
      keywords = list(set(list(keywords) + list(llm_keywords)))
      # 3根据关键值从es中召回字段值
      value_maps: dict[str,ValueInfo] = {}
      for keyword in keywords:
         # 3.1 从es中召回字段值
         values: list[ValueInfo] = await value_es_repository.recall_values(keyword)
         # 3.3 去重
         for value in values:
            if value.id not in value_maps:
               value_maps[value.id] = value
      writer({"type": "progress", "step": "召回字段取值", "status": "success"})
      logger.info(f"成功从Elasticsearch中召回{len(value_maps)}个字段值: {[value.value for value in list(value_maps.values())]}")  
      return {"retrieved_values_infos": list(value_maps.values())}   
   except Exception as e:
      writer({"type": "progress", "step": "召回字段取值", "status": "error"})
      logger.error(f"召回字段取值失败: {e}")
      raise Exception(f"召回字段取值失败: {e}")
       