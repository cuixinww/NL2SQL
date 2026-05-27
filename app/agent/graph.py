from langchain_core.messages import content
from langgraph.graph import StateGraph,START,END
from app.agent.context import ContextSchema
from app.agent.state import DataAgentState
from app.repositories.qdrant import ColumnQdrantRepository
from app.repositories.qdrant import MetricQdrantRepository
from app.repositories.es import ValueESRepository
from app.repositories.mysql.meta import MetaMySQLRepository
from app.repositories.mysql.dw import DWMySQLRepository
from app.clients import embedding_client_manager
from app.clients import qdrant_client_manager
from app.clients import es_client_manager
from app.clients import meta_mysql_client_manager
from app.clients import dw_mysql_client_manager
from app.agent.nodes import *
import asyncio

# 构建状态图
graph_builder = StateGraph(state_schema=DataAgentState, context_schema=ContextSchema)
#添加节点
graph_builder.add_node("add_extra_context", add_extra_context)
graph_builder.add_node("correct_sql", correct_sql)
graph_builder.add_node("execute_sql", execute_sql)
graph_builder.add_node("extract_keywords", extract_keywords)
graph_builder.add_node("filter_metric", filter_metric)
graph_builder.add_node("filter_table", filter_table)
graph_builder.add_node("generate_sql", generate_sql)
graph_builder.add_node("merge_retrieved_info", merge_retrieved_info)
graph_builder.add_node("recall_column", recall_column)
graph_builder.add_node("recall_metric", recall_metric)
graph_builder.add_node("recall_value", recall_value)
graph_builder.add_node("validate_sql", validate_sql)

#添加边
graph_builder.add_edge(START, "extract_keywords")
graph_builder.add_edge("extract_keywords", "recall_column")
graph_builder.add_edge("extract_keywords", "recall_value")
graph_builder.add_edge("extract_keywords", "recall_metric")
graph_builder.add_edge("recall_column", "merge_retrieved_info")
graph_builder.add_edge("recall_value", "merge_retrieved_info")
graph_builder.add_edge("recall_metric", "merge_retrieved_info")
graph_builder.add_edge("merge_retrieved_info", "filter_metric")
graph_builder.add_edge("merge_retrieved_info", "filter_table")
graph_builder.add_edge("filter_metric", "add_extra_context")
graph_builder.add_edge("filter_table", "add_extra_context")
graph_builder.add_edge("add_extra_context", "generate_sql")
graph_builder.add_edge("generate_sql", "validate_sql")
def _after_validate(state):
    if state["error"] is None:
        return "execute_sql"
    # 最大重试 3 次
    retry_count = state.get("retry_count") or 0
    if retry_count >= 3:
        return "execute_sql"
    return "correct_sql"

graph_builder.add_conditional_edges("validate_sql",
                                    _after_validate,
                                    {"execute_sql": "execute_sql", "correct_sql": "correct_sql"})

graph_builder.add_edge("correct_sql", "validate_sql")
graph_builder.add_edge("execute_sql", END)

graph = graph_builder.compile()

# print(graph.get_graph().draw_mermaid())

if __name__ == "__main__":

    async def main():
        qdrant_client_manager.init()
        embedding_client_manager.init()
        es_client_manager.init()
        meta_mysql_client_manager.init()
        dw_mysql_client_manager.init()


        query = "统计华北地区的销售总额。"
        input = DataAgentState(query=query)
        async with meta_mysql_client_manager.session_factory() as meta_Session, \
             dw_mysql_client_manager.session_factory() as dw_Session:
            column_qdrant_repository = ColumnQdrantRepository(qdrant_client_manager.client)
            metric_qdrant_repository = MetricQdrantRepository(qdrant_client_manager.client)
            value_es_repository = ValueESRepository(es_client_manager.es_client)
            meta_mysql_repository = MetaMySQLRepository(meta_Session)
            dw_mysql_repository = DWMySQLRepository(dw_Session)

            content = ContextSchema(
                column_qdrant_repository=column_qdrant_repository,
                metric_qdrant_repository=metric_qdrant_repository,
                value_es_repository=value_es_repository,
                embedding_client=embedding_client_manager.client,
                meta_repository=meta_mysql_repository,
                dw_mysql_repository=dw_mysql_repository
                )
        
            async for chunk in graph.astream(input=input,context=content,stream_mode="custom"):
                print(chunk)

        await qdrant_client_manager.close()
        await es_client_manager.close()
        await meta_mysql_client_manager.close()


    asyncio.run(main())