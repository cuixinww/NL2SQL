from app.agent.context import ContextSchema
from app.core import logger
from app.agent.context import ContextSchema
from app.agent.state import DataAgentState
from app.agent.llm import create_llm
from app.prompt import load_prompt
from langgraph.runtime import Runtime
from langchain_core.prompts import PromptTemplate
from langchain_core.output_parsers import JsonOutputParser
from app.agent.state import TableInfoState
import yaml

async def filter_table(state: DataAgentState, runtime: Runtime[ContextSchema]):
    logger.info("开始过滤表信息")
    writer = runtime.stream_writer
    writer({"type": "progress", "step": "过滤表格", "status": "running"})
    try:
        query = state["query"]
        table_infos: list[TableInfoState] = state["table_infos"]
        # 1 使用llm补充关键词
        llm = create_llm()
        # 1.1 创建提示词
        prompt_template = load_prompt("filter_table_info")
        prompt = PromptTemplate.from_template(template=prompt_template)
        # 1.2 创建执行链
        chain = prompt | llm | JsonOutputParser()

        result = await chain.ainvoke({"query": query, 
                "table_infos": yaml.safe_dump(table_infos, allow_unicode=True, sort_keys=False)})
        result = dict(result)
        # 2 过滤后表信息
        filter_table_infos: list[TableInfoState] = []
        for table_info in table_infos:
        # 2.1 确认过滤后表是否存在
                if table_info["name"] in result.keys():
                    table_info["columns"] = [ column for column in table_info["columns"] if column["name"] in result[table_info["name"]]]
                    filter_table_infos.append(table_info)

        writer({"type": "progress", "step": "过滤表格", "status": "success"})
        logger.info(f"成功过滤表信息: {[table_info['name'] for table_info in filter_table_infos]}")
        return {"table_infos": filter_table_infos}
    except Exception as e:
        writer({"type": "progress", "step": "过滤表格", "status": "error"})
        logger.error(f"过滤表格信息失败: {e}")
        raise Exception(f"过滤表格信息失败: {e}")
        