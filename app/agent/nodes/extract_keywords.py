from app.core import logger
from app.agent.context import ContextSchema
from app.agent.state import DataAgentState
from langgraph.runtime import Runtime
import jieba
import jieba.analyse
from pathlib import Path

# 加载银行术语词典
_BANK_TERM_DICT_PATH = Path(__file__).parents[3] / 'prompts' / 'bank_term_dict.txt'
if _BANK_TERM_DICT_PATH.exists():
    jieba.load_userdict(str(_BANK_TERM_DICT_PATH))

# 银行场景停用词
_BANK_STOPWORDS = {"银行", "请问", "帮我", "查一下", "多少", "什么", "怎么"}

async def extract_keywords(state: DataAgentState, runtime: Runtime[ContextSchema]):
    logger.info("开始抽取关键词")
    writer = runtime.stream_writer
    writer({"type": "progress", "step": "抽取关键字", "status": "running"})

    try:
        query = state["query"]
        allow_pos = (
            "n", "nr", "ns", "nt", "nz",
            "v", "vn",
            "a", "an",
            "eng", "i", "l",
        )
        keywords = jieba.analyse.extract_tags(query, topK=20, allowPOS=allow_pos)
        # 过滤银行停用词
        keywords = [w for w in keywords if w not in _BANK_STOPWORDS]
        keywords = list(set(keywords + [query]))
        writer({"type": "progress", "step": "抽取关键字", "status": "success"})
        logger.info(f"成功抽取关键词: {keywords}")
        return {"keywords": keywords}

    except Exception as e:
        keywords = []
        writer({"type": "progress", "step": "抽取关键字", "status": "error"})
        logger.error(f"抽取关键词失败: {e}")
        raise Exception(f"抽取关键词失败: {e}")
