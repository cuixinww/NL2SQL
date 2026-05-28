from app.agent.context import ContextSchema
from app.agent.state import DataAgentState
from langgraph.runtime import Runtime
from app.core import logger
from app.agent.llm import create_llm
from app.prompt import load_prompt
from langchain_core.prompts import PromptTemplate
from langchain_core.output_parsers import JsonOutputParser
import yaml



async def validate_sql(state: DataAgentState, runtime: Runtime[ContextSchema]):
    logger.info("开始验证SQL")
    writer = runtime.stream_writer
    writer({"type": "progress", "step": "验证SQL", "status": "running"})
    retry_count = state.get("retry_count") or 0
    violations = []
    suggestions = []
    try:
        sql = state["sql"]
        query = state["query"]
        table_infos = state["table_infos"]
        metric_infos = state["metric_infos"]
        date_info = state["date_info"]
        db_info = state["db_info"]
        # 1 使用llm验证sql是否符合语法
        llm = create_llm()
        # 1.1 创建提示词
        prompt_template = load_prompt("validate_sql")
        prompt = PromptTemplate.from_template(template=prompt_template)
        # 1.2 创建执行链
        chain = prompt | llm | JsonOutputParser()
        validate_result = await chain.ainvoke({
                            "query": query,
                            "sql": sql,
                            "table_infos": yaml.safe_dump(table_infos, allow_unicode=True, sort_keys=False),
                            "metric_infos": yaml.safe_dump(metric_infos, allow_unicode=True, sort_keys=False),
                            "date_info": yaml.safe_dump(date_info, allow_unicode=True, sort_keys=False),
                            "db_info": yaml.safe_dump(db_info, allow_unicode=True, sort_keys=False)
                            }
        )

        # 检查是否有违规
        violations = validate_result.get("violations", [])
        suggestions = validate_result.get("suggestions", [])
        if violations:
            violation_text = "; ".join(violations)
            raise Exception(f"SQL校验不通过: {violation_text}")

        # 2 使用explain验证sql是否符合语法
        await runtime.context.bank_mysql_repository.validate_sql(sql)
        writer({"type": "progress", "step": "验证SQL", "status": "success"})
        logger.info(f"SQL验证成功: {sql}")
        return {"error": None, "violations": [], "suggestions": [], "retry_count": retry_count}
    except Exception as e:
        writer({"type": "progress", "step": "验证SQL", "status": "running"})
        logger.error(f"SQL验证失败: {e}")
        return {
            "error": str(e),
            "suggestions": suggestions,
            "violations": violations if violations else [str(e)],
            "retry_count": retry_count + 1
        }
