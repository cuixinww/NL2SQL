from langchain.chat_models import init_chat_model
from app.conf import app_config
from langchain_core.language_models import BaseChatModel

def create_llm(
    model_name: str | None = None,
    temperature: float = 0,
    streaming: bool = False,
    timeout: int = 60,) -> BaseChatModel:

    return init_chat_model(
        model=model_name or app_config.llm.model_name,
        model_provider="openai",
        api_key=app_config.llm.api_key,
        base_url=app_config.llm.base_url,
        temperature=temperature,
        streaming=streaming,
        verbose=False,
        timeout=timeout,
    )


if __name__ == "__main__":
    llm = create_llm()
    print(llm.invoke(input="你好").content)
   