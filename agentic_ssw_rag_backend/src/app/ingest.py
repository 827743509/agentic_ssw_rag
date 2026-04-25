import argparse
from pathlib import Path


from llama_index.core import SimpleDirectoryReader, Settings
from llama_index.core.ingestion import IngestionPipeline
from llama_index.core.node_parser import SentenceSplitter

from app.config import get_settings
from app.embedding import build_embed_model
from app.vector_store import build_vector_store


DEFAULT_EXTS = [
    ".txt",
    ".md",
    ".pdf",
    ".docx",
    ".pptx",
    ".csv",
    ".xlsx",
]


def load_documents(data_dir: str):
    path = Path(data_dir)
    if not path.exists():
        raise FileNotFoundError(f"data_dir not found: {path.resolve()}")

    documents = SimpleDirectoryReader(

        input_dir=str(path),
        recursive=True,
        required_exts=DEFAULT_EXTS,
    ).load_data()


    for doc in documents:
        doc.metadata = {
            **(doc.metadata or {}),
            "source_path": doc.metadata.get("file_path") or doc.metadata.get("file_name", ""),
        }

    return documents


def ingest_directory(data_dir: str, overwrite: bool = False) -> int:
    settings = get_settings()
    embed_model = build_embed_model()

    Settings.embed_model = embed_model
    Settings.llm = None

    documents = load_documents(data_dir)

    vector_store = build_vector_store(overwrite=overwrite)

    pipeline = IngestionPipeline(
        transformations=[
            SentenceSplitter(
                chunk_size=settings.chunk_size,
                chunk_overlap=settings.chunk_overlap,
            ),
            embed_model,
        ],
        vector_store=vector_store,
    )

    nodes = pipeline.run(documents=documents, show_progress=True)
    return len(nodes)


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--data-dir", default="D:/project/agentic_rag_llamaindex/data")
    parser.add_argument("--overwrite", action="store_true")
    args = parser.parse_args()

    count = ingest_directory(
        data_dir=args.data_dir,
        overwrite=args.overwrite,
    )
    print(f"Indexed nodes: {count}")


if __name__ == "__main__":
    main()
