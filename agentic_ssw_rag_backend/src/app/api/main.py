import os
from datetime import date
from pathlib import Path

from fastapi import APIRouter, FastAPI
from fastapi.responses import FileResponse, StreamingResponse
from fastapi.staticfiles import StaticFiles
from llama_index.observability.otel import LlamaIndexOpenTelemetry
from opentelemetry.exporter.otlp.proto.http.trace_exporter import OTLPSpanExporter

from app.api.documents import router as documents_router
from app.api.exceptions import register_exception_handlers
from app.api.schemas import ChatRequest, QueryRequest, QueryResponse, SourceChunk
from app.core.config import BASE_DIR
from app.utils.agent import build_agent_workflow, build_graph_agent
from app.utils.rag import query_knowledge_base, stream_knowledge_base


router = APIRouter(prefix="/agent")


@router.post("/rag", response_model=QueryResponse)
async def rag_query(req: QueryRequest):
    result = query_knowledge_base(
        question=req.question,
        access_tags=req.access_tags,
        top_k=req.top_k,
    )

    return QueryResponse(
        answer=result["answer"],
        sources=[
            SourceChunk(
                score=s.get("score"),
                text=s.get("text", ""),
                metadata=s.get("metadata", {}),
            )
            for s in result["sources"]
        ],
    )


@router.post("/chat")
async def agent_chat(req: ChatRequest):
    return StreamingResponse(
        stream_knowledge_base(
            question=req.question,
            access_tags=req.access_tags,
            top_k=req.top_k,
        ),
        media_type="text/plain; charset=utf-8",
        headers={
            "Cache-Control": "no-cache",
            "X-Accel-Buffering": "no",
        },
    )


@router.post("/graph", response_model=QueryResponse)
async def agent_graph(req: ChatRequest):
    agent = build_graph_agent()
    message = f"""
当前日期是：{date.today().isoformat()}
用户问题：{req.question}
"""
    handler = agent.run(message)
    response = await handler

    return QueryResponse(answer=str(response))


@router.post("/search", response_model=QueryResponse)
async def agent_search(req: ChatRequest):
    workflow = build_agent_workflow()
    message = f"""
当前日期是：{date.today().isoformat()}
用户问题：{req.question}
"""
    response = await workflow.run(user_msg=message)

    return QueryResponse(answer=str(response))


def include_api_routes(app: FastAPI) -> None:
    app.include_router(router)
    app.include_router(documents_router)

    api_router = APIRouter(prefix="/api")
    api_router.include_router(router)
    api_router.include_router(documents_router)
    app.include_router(api_router)


def register_frontend(app: FastAPI) -> None:
    frontend_dist = Path(os.getenv("FRONTEND_DIST_DIR", BASE_DIR / "frontend_dist")).resolve()
    index_path = frontend_dist / "index.html"
    if not index_path.exists():
        return

    assets_dir = frontend_dist / "assets"
    if assets_dir.exists():
        app.mount("/assets", StaticFiles(directory=assets_dir), name="frontend-assets")

    @app.get("/{full_path:path}", include_in_schema=False)
    async def serve_frontend(full_path: str):
        requested_path = (frontend_dist / full_path).resolve()
        if requested_path.is_file() and frontend_dist in requested_path.parents:
            return FileResponse(requested_path)
        return FileResponse(index_path)


def create_app() -> FastAPI:
    app = FastAPI()

    register_exception_handlers(app)
    include_api_routes(app)

    your_span_exporter = OTLPSpanExporter(
        endpoint="http://localhost:6006/v1/traces",
    )

    instrumentor = LlamaIndexOpenTelemetry(
        span_exporter=your_span_exporter,
        service_name_or_resource="llamaIndex-rag",
        span_processor="batch",
        debug=True,
    )
    instrumentor.start_registering()

    register_frontend(app)
    return app


app = create_app()
