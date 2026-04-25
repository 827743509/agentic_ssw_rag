from functools import lru_cache

from llama_index.embeddings.huggingface import HuggingFaceEmbedding

from .config import get_settings


@lru_cache(maxsize=1)
def build_embed_model() -> HuggingFaceEmbedding:
    settings = get_settings()

    device = None if settings.embed_device == "auto" else settings.embed_device

    # Qwen3 Embedding 在检索场景建议给 query 加 instruction。
    query_instruction = (
        "给定一个用户问题，检索能够回答该问题的相关文档片段"
    )

    return HuggingFaceEmbedding(
        model_name=settings.embed_model_name,
        max_length=settings.embed_max_length,
        embed_batch_size=settings.embed_batch_size,
        device=device,
        trust_remote_code=True,
        normalize=True,
        query_instruction=query_instruction,
        show_progress_bar=True,
    )
