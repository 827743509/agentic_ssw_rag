from llama_index.vector_stores.milvus import MilvusVectorStore
from llama_index.vector_stores.milvus.utils import BM25BuiltInFunction

from .config import get_settings


def build_vector_store(overwrite: bool | None = None) -> MilvusVectorStore:
    settings = get_settings()

    if overwrite is None:
        overwrite = settings.milvus_overwrite


    index_config = {
        "index_type": "HNSW",
        "metric_type": "COSINE",
        "params": {"M": 16, "efConstruction": 200},
    }

    search_config = {
        "ef": 64
    }
    bm25_function = BM25BuiltInFunction(
        analyzer_params={
            "type": "chinese"
        },
        enable_match=True,
    )
    return MilvusVectorStore(
        uri=settings.milvus_uri,
        token=settings.milvus_token,
        collection_name=settings.milvus_collection,
        dim=settings.embed_dim,
        # 开启稀疏检索 / BM25
        enable_sparse=True,
        overwrite=overwrite,
        similarity_metric="COSINE",
        index_config=index_config,
        search_config=search_config,
        consistency_level="Session",
        # sparse/BM25 索引配置
        sparse_embedding_function=bm25_function,
        sparse_index_config={
          "index_type": "SPARSE_INVERTED_INDEX",
          "metric_type": "BM25",
          "params": {
            "type": "chinese",
            "inverted_index_algo": "DAAT_MAXSCORE",
            "bm25_k1": 1.2,
            "bm25_b": 0.75,
          },
        },
        # 关键配置：加权融合
        hybrid_ranker="WeightedRanker",
        hybrid_ranker_params={
        "weights": [0.7, 0.3]  # dense 向量 0.7，BM25 0.3
       },
    )
