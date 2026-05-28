from dataclasses import dataclass
from app.repositories.qdrant import ColumnQdrantRepository
from app.repositories.qdrant import MetricQdrantRepository
from app.repositories.es import ValueESRepository
from app.repositories.mysql.meta import MetaMySQLRepository
from app.repositories.mysql.bank import BankMySQLRepository
from langchain_openai import OpenAIEmbeddings


@dataclass
class ContextSchema:
    column_qdrant_repository: ColumnQdrantRepository
    metric_qdrant_repository: MetricQdrantRepository
    value_es_repository: ValueESRepository
    embedding_client: OpenAIEmbeddings
    meta_repository: MetaMySQLRepository
    bank_mysql_repository: BankMySQLRepository

