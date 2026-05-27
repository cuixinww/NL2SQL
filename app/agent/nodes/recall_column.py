from app.core import logger
from app.agent.context import ContextSchema
from app.agent.state import DataAgentState
from app.agent.llm import create_llm
from app.prompt import load_prompt
from app.entities import ColumnInfo
from langgraph.runtime import Runtime
from langchain_core.prompts import PromptTemplate
from langchain_core.output_parsers import JsonOutputParser



async def recall_column(state: DataAgentState, runtime: Runtime[ContextSchema]):
   logger.info("开始从Qdrant数据库中召回字段信息")
   writer = runtime.stream_writer
   writer({"type": "progress", "step": "召回字段", "status": "running"})
   try:
      keywords = state["keywords"]
      query = state["query"]
      # 根据关键词，从qdradn数据库中召回字段信息
      # 1 获取qdrant仓库
      column_qdrant_repository = runtime.context.column_qdrant_repository
      # 2 使用llm补充关键词
      llm = create_llm()
      # 2.1 创建提示词
      prompt_template = load_prompt("extend_keywords_for_column_recall")
      prompt = PromptTemplate.from_template(template=prompt_template)
      # 2.2 创建执行链
      chain = prompt | llm | JsonOutputParser()
      llm_keywords = await chain.ainvoke(query)
      logger.info(f"成功补充关键词: {llm_keywords}")
      # 2.3 合并关键词，并去重
      keywords = list(set(list(keywords) + list(llm_keywords)))
      # 3 从qdrant中召回字段信息
      column_maps: dict[str,ColumnInfo] = {}
      for keyword in keywords:
         # 3.1 将关键词向量化
         embedding = await runtime.context.embedding_client.aembed_query(keyword)
         # 3.2 从qdrant中召回字段信息
         column_infos: list[ColumnInfo] = await column_qdrant_repository.recall_columns(embedding)
         # 3.3 去重
         for column_info in column_infos:
            if column_info.id not in column_maps:
               column_maps[column_info.id] = column_info
      writer({"type": "progress", "step": "召回字段", "status": "success"})
      logger.info(f"成功从Qdrant数据库中召回{len(column_maps)}个字段信息: {[column_info.name for column_info in list(column_maps.values())]}")  
      return {"retrieved_column_infos": list(column_maps.values())}
   except Exception as e:
      writer({"type": "progress", "step": "召回字段", "status": "error"})
      logger.error(f"召回字段信息失败: {e}")
      raise Exception(f"召回字段信息失败: {e}")
       
