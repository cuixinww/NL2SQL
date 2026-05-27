from app.core import logger
from app.agent.context import ContextSchema
from app.agent.state import DataAgentState
from app.agent.llm import create_llm
from app.prompt import load_prompt
from langgraph.runtime import Runtime
from langchain_core.prompts import PromptTemplate
from langchain_core.output_parsers import StrOutputParser
import yaml


async def generate_sql(state: DataAgentState, runtime: Runtime[ContextSchema]):
    logger.info("开始生成SQL")
    writer = runtime.stream_writer
    writer({"type": "progress", "step": "生成SQL", "status": "running"})
    try:
        query = state["query"]
        table_infos = state["table_infos"]
        metric_infos = state["metric_infos"]
        date_info = state["date_info"]
        db_info = state["db_info"]
        join_paths = state.get("join_paths", [])

        llm = create_llm()
        prompt_template = load_prompt("generate_sql")
        prompt = PromptTemplate.from_template(template=prompt_template)
        chain = prompt | llm | StrOutputParser()
        llm_sql = await chain.ainvoke({
            "query": query,
            "table_infos": yaml.safe_dump(table_infos, allow_unicode=True, sort_keys=False),
            "metric_infos": yaml.safe_dump(metric_infos, allow_unicode=True, sort_keys=False),
            "date_info": yaml.safe_dump(date_info, allow_unicode=True, sort_keys=False),
            "db_info": yaml.safe_dump(db_info, allow_unicode=True, sort_keys=False),
            "join_paths": yaml.safe_dump(join_paths, allow_unicode=True, sort_keys=False)
        })

        if "```sql" in llm_sql:
            llm_sql = llm_sql.replace("```sql", "").replace("```", "").strip()
        llm_sql = " ".join(llm_sql.split())

        writer({"type": "progress", "step": "生成SQL", "status": "success"})
        logger.info(f"成功生成SQL: {llm_sql}")
        return {"sql": llm_sql}
    except Exception as e:
        writer({"type": "progress", "step": "生成SQL", "status": "error"})
        logger.error(f"生成SQL失败: {e}")
        raise Exception(f"生成SQL失败: {e}")
