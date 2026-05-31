from functools import lru_cache
from typing import Generator, List, Optional

from llama_index.core import Settings, VectorStoreIndex
from llama_index.core.prompts import PromptTemplate
from llama_index.core.vector_stores import MetadataFilters

from app.core.config import get_settings
from app.db.vector_store import build_vector_store
from app.utils.embedding import build_embed_model
from app.utils.llm import build_llm, build_moonshot_llm

# from app.utils.qwen_rerank_postprocessor import Qwen3RerankPostprocessor


QA_TEMPLATE = PromptTemplate(
    """你是知识库助手。

要求：
1. 必须优先依据下面的知识库内容回答。
2. 如果知识库没有依据，明确说“知识库中没有找到足够依据”，不要编造。
3. 回答要结构化，必要时列步骤、条件、注意事项。
4. 最后给出“依据摘要”。

知识库内容：
---------------------
{context_str}
---------------------

用户问题：{query_str}

请用中文回答：
"""
)


@lru_cache(maxsize=1)
def build_index() -> VectorStoreIndex:
    embed_model = build_embed_model()
    Settings.embed_model = embed_model
    Settings.llm = build_llm()

    vector_store = build_vector_store(overwrite=False)

    # 这里不会重新入库，只是把已有 Milvus collection 包装成 LlamaIndex index
    return VectorStoreIndex.from_vector_store(
        vector_store=vector_store,
        embed_model=embed_model,
    )


def build_metadata_filters(
    access_tags: Optional[List[str]] = None,
) -> MetadataFilters:
    # 最基本的多租户过滤：只能检索当前 tenant_id 的文档。
    filters = [

    ]

    # 权限标签可以继续扩展：
    # - 文档入库时写 metadata["access_tags"] = ["finance", "hr"]
    # - 查询时根据用户角色加 FilterOperator.IN / CONTAINS
    # 不同 Milvus / LlamaIndex 版本对 list metadata filter 支持有差异，所以模板先预留。
    _ = access_tags

    return MetadataFilters(filters=filters)


def build_query_engine(
    access_tags: Optional[List[str]] = None,
    top_k: Optional[int] = None,
    streaming: bool = False,
):
    settings = get_settings()
    index = build_index()
    # reranker = Qwen3RerankPostprocessor(
    #     top_n=5,
    #     batch_size=4,
    # )
    return index.as_query_engine(
        llm=build_moonshot_llm(),
        similarity_top_k=top_k or settings.similarity_top_k,
        # node_postprocessors=[reranker],
        filters=build_metadata_filters( access_tags=access_tags),
        vector_store_query_mode="hybrid",
        response_mode="compact",
        text_qa_template=QA_TEMPLATE,
        streaming=streaming,
    )


def build_retriever(
    access_tags: Optional[List[str]] = None,
    top_k: Optional[int] = None,
):
    settings = get_settings()
    index = build_index()
    return index.as_retriever(
        similarity_top_k=top_k or settings.similarity_top_k,
        filters=build_metadata_filters(access_tags=access_tags),
        vector_store_query_mode="hybrid",
    )


def query_knowledge_base(
    question: str,
    access_tags: Optional[List[str]] = None,
    top_k: Optional[int] = None,
):
    query_engine = build_query_engine(
        access_tags=access_tags or [],
        top_k=top_k,
    )

    response = query_engine.query(question)

    sources = []
    for node in getattr(response, "source_nodes", []) or []:
        sources.append(
            {
                "score": getattr(node, "score", None),
                "text": node.node.get_content()[:1200],
                "metadata": node.node.metadata or {},
            }
        )

    return {
        "answer": str(response),
        "sources": sources,
    }


def stream_knowledge_base(
    question: str,
    access_tags: Optional[List[str]] = None,
    top_k: Optional[int] = None,
) -> Generator[str, None, None]:
    yield "\n"

    try:
        retriever = build_retriever(
            access_tags=access_tags or [],
            top_k=top_k,
        )
        nodes = retriever.retrieve(question)

        if not nodes:
            yield "知识库中没有找到足够依据。"
            return

        context_str = "\n\n".join(
            node.node.get_content()
            for node in nodes
            if node.node.get_content()
        )
        if not context_str.strip():
            yield "知识库中没有找到足够依据。"
            return

        prompt = QA_TEMPLATE.format(
            context_str=context_str,
            query_str=question,
        )

        llm = build_moonshot_llm()
        emitted = False
        final_text = ""
        for response in llm.stream_complete(prompt):
            chunk = getattr(response, "delta", None)
            if chunk is None:
                text = getattr(response, "text", "") or ""
                chunk = text[len(final_text):] if text.startswith(final_text) else text
                final_text = text

            if not chunk:
                continue
            emitted = True
            yield chunk

        if not emitted:
            yield "未返回回答。"
    except Exception as exc:
        yield f"\n\n请求失败：{exc}"
