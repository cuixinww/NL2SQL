# import sys
# from pathlib import Path
# sys.path.insert(0, str(Path(__file__).parents[2]))
from typing import Optional
from app.conf import EmbeddingConfig, app_config, LLMConfig
from langchain_openai import OpenAIEmbeddings
from app.core import logger



class EmbeddingClientManager:
    
    def __init__(self, embedding_config: EmbeddingConfig, llm_config: LLMConfig ):
        """
        初始化Embedding客户端管理器
        :param embedding_config: Embedding配置
        :param llm_config: LLM配置
        """
        self.client: Optional[OpenAIEmbeddings] = None
        self.llm_config: LLMConfig = llm_config
        self.embedding_config: EmbeddingConfig = embedding_config

    def init(self):
        """
        初始化Embedding客户端
        :return: None
        """
        logger.info("初始化Embedding客户端")
        if self.embedding_config.use_openai:
            self.client = OpenAIEmbeddings(
                model=self.llm_config.embedding_model,
                api_key=self.llm_config.api_key,
                base_url=self.llm_config.base_url,
                check_embedding_ctx_length=False,
            )
  
        else:
            self.client = OpenAIEmbeddings(
                model=self.embedding_config.model,
                api_key="dummy-key",
                base_url= self._get_url(),
                check_embedding_ctx_length=False,
            )
        logger.info("Embedding客户端初始化完成")

    def _get_url(self):
        """
        获取Embedding模型URL
        :return: str
        """
        return f"http://{self.embedding_config.host}:{self.embedding_config.port}/v1"
        


# 初始化全局Embedding客户端管理器
embedding_client_manager = EmbeddingClientManager(app_config.embedding, app_config.llm)

if __name__ == '__main__':
    embedding_client_manager.init()
    client = embedding_client_manager.client
    res = client.embed_query("Hello, World!")
    print(res[:5])
                 
