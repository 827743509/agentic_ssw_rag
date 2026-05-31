
from functools import lru_cache


from llama_index.llms.dashscope import DashScope
from llama_index.llms.openai import OpenAI
from llama_index.llms.openai_like import OpenAILike

from app.core.config import get_settings


@lru_cache(maxsize=1)
def build_llm() -> DashScope:
    settings = get_settings()

    return DashScope(model_name=settings.qwen_llm_model,api_key=settings.dashscope_api_key,max_tokens=settings.dashscope_max_tokens)


@lru_cache(maxsize=1)
def build_moonshot_llm() -> OpenAI:
    settings = get_settings()

    return OpenAILike(
        model=settings.kimi_llm_model,
        api_key=settings.kimi_api_key,
        api_base=settings.kimi_base_url,
        is_chat_model=True,
        is_function_calling_model=True,
        max_tokens=settings.kimi_max_tokens,
        temperature=0.6,
        additional_kwargs={
            "extra_body": {
                "thinking": {"type": "disabled"}
            }
        },
    )

