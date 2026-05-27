from app.agent.context import ContextSchema
from app.agent.state import DataAgentState
from langgraph.runtime import Runtime
from app.entities import ColumnInfo, MetricInfo, ValueInfo, TableInfo
from app.core import logger
from app.agent.state import ColumnInfoState, TableInfoState, MetricInfoState
from collections import defaultdict, deque


def _build_join_paths(table_column_infos: dict[str, list[ColumnInfo]], table_relations: list) -> list[str]:
    """
    通过外键推导 JOIN 路径
    """
    # 1. 构建邻接表（外键关系）
    adjacency = defaultdict(list)  # table_id -> [(ref_table_id, local_col, ref_col)]

    for table_id, columns in table_column_infos.items():
        for col in columns:
            if col.role == "foreign_key" and col.ref_table_id and col.ref_column_id:
                adjacency[table_id].append((col.ref_table_id, col.name, col.ref_column_id.split(".")[-1]))

    # 2. BFS 遍历生成 JOIN 路径
    table_ids = list(table_column_infos.keys())
    if len(table_ids) <= 1:
        return []

    join_paths = []
    visited = set()
    # 优先以有外键且指向 table_ids 内部的表为起点，确保 BFS 能遍历到关联表
    start = table_ids[0]
    for tid in table_ids:
        if any(ref in table_ids for ref, _, _ in adjacency.get(tid, [])):
            start = tid
            break
    queue = deque([start])
    visited.add(start)

    while queue:
        current = queue.popleft()
        for ref_table, local_col, ref_col in adjacency.get(current, []):
            if ref_table in table_ids and ref_table not in visited:
                # 生成 JOIN 路径
                current_alias = current.split(".")[-1][0]
                ref_alias = ref_table.split(".")[-1][0]
                join_path = f"JOIN {ref_table} {ref_alias} ON {current_alias}.{local_col} = {ref_alias}.{ref_col}"
                join_paths.append(join_path)
                visited.add(ref_table)
                queue.append(ref_table)

    # 3. 如果外键路径不连通，查询 table_relation 补充
    unreachable = set(table_ids) - visited
    if unreachable and table_relations:
        for rel in table_relations:
            left_in = rel.left_table_id in table_column_infos
            right_in = rel.right_table_id in table_column_infos
            left_visited = rel.left_table_id in visited
            right_visited = rel.right_table_id in visited

            if left_in and right_in:
                if (left_visited and not right_visited) or (right_visited and not left_visited):
                    join_paths.append(f"JOIN {rel.right_table_id} ON {rel.join_condition}")
                    visited.add(rel.right_table_id)
                    visited.add(rel.left_table_id)

    return join_paths


async def merge_retrieved_info(state: DataAgentState, runtime: Runtime[ContextSchema]):
    logger.info("开始合并召回信息")
    writer = runtime.stream_writer
    writer({"type": "progress", "step": "合并召回信息", "status": "running"})
    try:
        retrieved_column_infos: list[ColumnInfo] = state["retrieved_column_infos"]
        retrieved_metric_infos: list[MetricInfo] = state["retrieved_metric_infos"]
        retrieved_values_infos: list[ValueInfo] = state["retrieved_values_infos"]

        # 1. 将指标信息的相关字段信息添加到字段信息中
        for metric_info in retrieved_metric_infos:
            for relevant_column in metric_info.relevant_columns:
                if relevant_column not in [column.id for column in retrieved_column_infos]:
                    column_info: ColumnInfo = await runtime.context.meta_repository.get_column_info_by_id(relevant_column)
                    if column_info:
                        retrieved_column_infos.append(column_info)

        # 2. 将字段值添加到其所属字段的example中
        for retrieved_value in retrieved_values_infos:
            column_id = retrieved_value.column_id
            value = retrieved_value.value
            if column_id not in [column.id for column in retrieved_column_infos]:
                column_info: ColumnInfo = await runtime.context.meta_repository.get_column_info_by_id(column_id)
                if column_info:
                    retrieved_column_infos.append(column_info)

            for column_info in retrieved_column_infos:
                if column_info.id == column_id and value not in column_info.examples:
                    column_info.examples.append(value)
                    break

        # 3. 按照表对字段信息进行分组
        table_column_infos: dict[str, list[ColumnInfo]] = {}
        for column_info in retrieved_column_infos:
            if column_info.table_id not in table_column_infos:
                table_column_infos[column_info.table_id] = []
            table_column_infos[column_info.table_id].append(column_info)

        # 4. 强制为每个表添加主外键字段
        for table_id in table_column_infos.keys():
            column_primary_info: list[ColumnInfo] = await runtime.context.meta_repository.get_primary_key_by_id(table_id)
            if column_primary_info:
                for col in column_primary_info:
                    if col.id not in [c.id for c in table_column_infos[table_id]]:
                        table_column_infos[table_id].append(col)

        # 5. JOIN 图推导
        table_relations = await runtime.context.meta_repository.get_table_relations_by_tables(list(table_column_infos.keys()))
        join_paths = _build_join_paths(table_column_infos, table_relations)

        # 6. 整形为 TableInfoState
        table_infos: list[TableInfoState] = []
        for table_id, column_infos in table_column_infos.items():
            table_info: TableInfo = await runtime.context.meta_repository.get_table_info_by_id(table_id)
            if table_info:
                table_infos.append(TableInfoState(
                    name=table_info.name,
                    description=table_info.description,
                    table_type=table_info.table_type,
                    db_schema=table_info.db_schema,
                    alias=table_info.alias,
                    columns=[
                        ColumnInfoState(
                            name=col.name,
                            data_type=col.data_type,
                            role=col.role,
                            examples=col.examples,
                            description=col.description,
                            alias=col.alias,
                            ref_table_id=col.ref_table_id,
                            ref_column_id=col.ref_column_id
                        )
                        for col in column_infos
                    ]
                ))

        # 7. 处理指标信息
        metric_infos: list[MetricInfoState] = [
            MetricInfoState(
                name=m.name,
                description=m.description,
                relevant_columns=m.relevant_columns,
                alias=m.alias,
                formula=m.formula,
                default_filter=m.default_filter
            )
            for m in retrieved_metric_infos
        ]

        writer({"type": "progress", "step": "合并召回信息", "status": "success"})
        logger.info(f"成功合并召回表信息: {[t['name'] for t in table_infos]}")
        logger.info(f"成功合并召回指标信息: {[m['name'] for m in metric_infos]}")
        logger.info(f"JOIN路径: {join_paths}")
        return {"table_infos": table_infos, "metric_infos": metric_infos, "join_paths": join_paths}

    except Exception as e:
        writer({"type": "progress", "step": "合并召回信息", "status": "error"})
        logger.error(f"合并召回信息失败: {e}")
        raise Exception(f"合并召回信息失败: {e}")
