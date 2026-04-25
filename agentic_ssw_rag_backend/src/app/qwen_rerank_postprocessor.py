from functools import lru_cache
from typing import Sequence

from pydantic import Field, PrivateAttr
from sentence_transformers import CrossEncoder

from llama_index.core.postprocessor.types import BaseNodePostprocessor
from llama_index.core.schema import NodeWithScore, QueryBundle, MetadataMode

from app.config import get_settings

settings=get_settings();
@lru_cache(maxsize=1)
def load_qwen_reranker() -> CrossEncoder:
    return CrossEncoder(
        settings.qwen3_reranker_model,
        trust_remote_code=True,
        local_files_only=True,
        max_length=8192,
        device="cuda",  # 没有 GPU 改成 "cpu"
    )


class Qwen3RerankPostprocessor(BaseNodePostprocessor):
    top_n: int = Field(default=5)
    batch_size: int = Field(default=4)

    _model: CrossEncoder = PrivateAttr()

    def __init__(self, top_n: int = 5, batch_size: int = 4):
        super().__init__(top_n=top_n, batch_size=batch_size)
        self._model = load_qwen_reranker()

    def _postprocess_nodes(
        self,
        nodes: Sequence[NodeWithScore],
        query_bundle: QueryBundle | None = None,
    ) -> list[NodeWithScore]:
        if query_bundle is None:
            return list(nodes)

        if not nodes:
            return []

        query = query_bundle.query_str

        documents = [
            node.node.get_content(metadata_mode=MetadataMode.NONE)
            for node in nodes
        ]

        pairs = [(query, doc) for doc in documents]

        scores = self._model.predict(
            pairs,
            batch_size=self.batch_size,
        )

        reranked_nodes: list[NodeWithScore] = []

        for node, score in zip(nodes, scores):
            node.score = float(score)
            reranked_nodes.append(node)

        reranked_nodes.sort(
            key=lambda x: x.score if x.score is not None else float("-inf"),
            reverse=True,
        )

        return reranked_nodes[: self.top_n]