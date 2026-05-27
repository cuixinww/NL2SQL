# 银行问数 — NL2SQL 智能查询系统

基于 LangGraph 构建的银行 OLTP 场景自然语言转 SQL 系统。用户输入自然语言问题，系统自动完成关键词提取、多路召回、SQL 生成、校验纠错、执行返回结果。

## 技术栈

| 组件 | 技术 |
|------|------|
| Agent 框架 | LangGraph + LangChain |
| LLM | OpenAI 兼容接口 |
| 向量数据库 | Qdrant（字段/指标语义召回） |
| 全文检索 | Elasticsearch（枚举值精准匹配） |
| 关系数据库 | MySQL 8.0（元数据 + 业务数据） |
| Embedding | BGE-Large-ZH-v1.5 |
| 后端框架 | FastAPI |
| 前端 | Vue 3 + Vite |

## 系统架构

```
用户问题
  │
  ▼
┌─────────────────────────────────────────────────────┐
│                  LangGraph Pipeline                  │
│                                                     │
│  extract_keywords                                   │
│       │                                             │
│       ├──► recall_column ──┐                        │
│       ├──► recall_metric ──┼──► merge_retrieved_info │
│       └──► recall_value ──┘         │               │
│                                     ▼               │
│                          filter_metric + filter_table│
│                                     │               │
│                                     ▼               │
│                             add_extra_context        │
│                                     │               │
│                                     ▼               │
│              generate_sql (公式拼装 + LLM 补全)       │
│                                     │               │
│                                     ▼               │
│              validate_sql ◄──► correct_sql (≤3次)    │
│                                     │               │
│                                     ▼               │
│                               execute_sql            │
└─────────────────────────────────────────────────────┘
  │
  ▼
查询结果
```

## 核心特性

- **外键推导 JOIN**：基于外键关系 BFS 遍历，自动生成多表 JOIN 路径
- **指标公式拼装**：从元数据 formula 字段提取聚合表达式，自动注入 default_filter
- **自包含子查询**：支持存贷比等跨表指标的子查询公式（如 `SELECT SUM(...) / SELECT SUM(...)`）
- **枚举值精准匹配**：通过 ES 全文检索精确匹配字段枚举值（网点名称、客户等级等）
- **校验纠错循环**：SQL 生成后经 LLM 校验 + EXPLAIN 验证，不通过则自动纠错（最多 3 次）

## 业务数据模型

```
branch (网点) ◄──── customer (客户) ◄──── account (账户)
    ▲                    │                    ▲
    │                    ▼                    │
    ├── employee (员工)  deposit_txn (存取流水) ┘
    │                    │
    ├── product (产品) ◄─┤
    │                    │
    ├── loan_contract (贷款合同)
    │                    │
    └── transfer_txn (转账流水)
```

8 张表：customer、account、branch、employee、product、deposit_txn、loan_contract、transfer_txn

14 个指标：deposit_balance、loan_balance、npl_rate、overdue_rate、ldr、avg_deposit_per_cust 等

## 快速开始

### 环境要求

- Python >= 3.12
- Docker + Docker Compose

### 1. 启动基础设施

```bash
cd docker
docker compose up -d
```

启动服务：
- MySQL 8.0（端口 3306）
- Elasticsearch 8.x（端口 9200）
- Qdrant（端口 6333）
- Embedding 服务 bge-large-zh-v1.5（端口 8081）
- Kibana（端口 5601）

### 2. 下载 Embedding 模型

从 HuggingFace 下载 `BAAI/bge-large-zh-v1.5` 模型文件，放置到：

```
docker/embedding/bge-large-zh-v1.5/
```

### 3. 安装依赖

```bash
pip install -e .
# 或使用 uv
uv sync
```

### 4. 配置文件

在 `conf/` 目录下创建配置文件（参考 data-agent 项目模板）：

- `conf/app_config.yaml` — 数据库连接、LLM 配置
- `conf/meta_config.yaml` — 表/字段/指标/表关系元数据定义

### 5. 构建元数据知识库

```bash
python -m app.scripts.build_meta_knowledge -c conf/meta_config.yaml
```

此步骤会：
- 将表/字段/指标/表关系写入 MySQL meta 库
- 将字段和指标的 embedding 向量写入 Qdrant
- 将 sync=true 的字段枚举值写入 Elasticsearch

### 6. 启动服务

```bash
python -m app.main
```

服务启动后访问 http://localhost:8000，前端页面默认在 http://localhost:5173。

## 项目结构

```
bank-agent/
├── app/
│   ├── agent/              # LangGraph Agent
│   │   ├── graph.py        # 状态图定义（12 节点）
│   │   ├── state.py        # 状态 Schema
│   │   ├── context.py      # 运行时上下文
│   │   ├── llm.py          # LLM 工厂
│   │   └── nodes/          # 各节点实现
│   │       ├── extract_keywords.py    # 关键词提取
│   │       ├── recall_column.py       # 字段语义召回
│   │       ├── recall_metric.py       # 指标语义召回
│   │       ├── recall_value.py        # 枚举值召回
│   │       ├── merge_retrieved_info.py # 信息合并 + JOIN 推导
│   │       ├── filter_metric.py       # 指标过滤
│   │       ├── filter_table.py        # 表过滤
│   │       ├── add_extra_context.py   # 业务口径注入
│   │       ├── generate_sql.py        # SQL 生成
│   │       ├── validate_sql.py        # SQL 校验
│   │       ├── correct_sql.py         # SQL 纠错
│   │       └── execute_sql.py         # SQL 执行
│   ├── api/                # FastAPI 接口
│   ├── clients/            # 外部服务客户端
│   ├── core/               # 日志、上下文
│   ├── entities/           # 领域实体
│   ├── models/             # ORM 模型
│   ├── prompt/             # 提示词加载器
│   ├── repositories/       # 数据访问层
│   │   ├── mysql/meta/     # 元数据 Repository
│   │   ├── mysql/dw/       # 业务数据 Repository
│   │   ├── qdrant/         # 向量召回 Repository
│   │   └── es/             # 枚举值 Repository
│   ├── scripts/            # 元数据构建脚本
│   └── services/           # 业务服务层
├── conf/                   # 配置文件（不入 git）
├── prompts/                # 提示词模板（不入 git）
├── docker/                 # Docker 基础设施
│   ├── docker-compose.yaml
│   ├── mysql/              # 初始化 SQL
│   ├── elasticsearch/      # ES + IK 分词器
│   └── embedding/          # Embedding 模型
└── main.py                 # FastAPI 入口
```

## 示例问题

| 类型 | 问题 |
|------|------|
| 统计 | 各分行本季度的存款余额 |
| 统计 | 各风险等级客户的不良贷款率 |
| 趋势 | 2025年各月存入金额变化趋势 |
| 对比 | 对比手机银行和网上银行的转账金额 |
| 明细 | 逾期超过90天的贷款明细 |
| 排名 | 存款余额排名前10的网点 |
| 复合 | 张三上个月通过柜台存了多少钱 |
| 跨表 | 当前存贷比是多少 |
| 画像 | 白金客户的人均存款 |

## License

MIT
