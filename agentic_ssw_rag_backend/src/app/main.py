import os
from datetime import date

from fastapi import Depends, FastAPI, APIRouter
from llama_index.observability.otel import LlamaIndexOpenTelemetry
from opentelemetry.exporter.otlp.proto.http.trace_exporter import OTLPSpanExporter
from prometheus_client import  Counter, Histogram, Gauge, generate_latest, CONTENT_TYPE_LATEST
from llama_index.core.workflow import Context
from app.agent import build_agent, build_graph_agent, build_agent_workflow
from app.config import get_settings
from app.models import ChatRequest, QueryRequest, QueryResponse, SourceChunk
from app.rag import query_knowledge_base
from app.security import verify_api_key
from fastapi import Response

router = APIRouter(
    prefix="/agent",
    dependencies=[Depends(verify_api_key)]
)
settings=get_settings()
def create_app() -> FastAPI:
    app = FastAPI()
    build_agent_workflow()
    app.include_router(router)

    return app


app = create_app()


# 简单内存会话。。
_AGENT_CONTEXTS: dict[str, Context] = {}






@app.post("/agent/rag", response_model=QueryResponse)
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


@app.post("/agent/chat", response_model=QueryResponse)
async def agent_chat(req: ChatRequest):
    # 根据租户 / 权限构建 agent。
    # 注意：如果每次请求都 build agent，
    agent = build_agent(
        access_tags=req.access_tags,
        top_k=req.top_k,
    )

    ctx_key = f"{req.session_id}"
    ctx = _AGENT_CONTEXTS.get(ctx_key)
    if ctx is None:
        ctx = Context(agent)
        _AGENT_CONTEXTS[ctx_key] = ctx

    handler = agent.run(req.question, ctx=ctx)
    response = await handler


    return QueryResponse(answer=str(response))



@app.post("/agent/graph", response_model=QueryResponse)
async def agent_chat(req: ChatRequest):
    # 根据租户 / 权限构建 agent。
    # 注意：如果每次请求都 build agent，会重复加载模型；生产环境建议做 agent / query_engine 缓存。
    agent = build_graph_agent()

    ctx_key = f"{req.session_id}"
    ctx = _AGENT_CONTEXTS.get(ctx_key)
    if ctx is None:
        ctx = Context(agent)
        _AGENT_CONTEXTS[ctx_key] = ctx
    message = f"""
    当前日期是：{date.today().isoformat()}
    用户问题：{req.question}
    """
    handler = agent.run(message, ctx=ctx)
    response = await handler


    return QueryResponse(answer=str(response))


@app.post("/agent/search", response_model=QueryResponse)
async def agent_search(req: ChatRequest):
    # 根据租户 / 权限构建 agent。
    # 注意：如果每次请求都 build agent，会重复加载模型；生产环境建议做 agent / query_engine 缓存。
    workflow = build_agent_workflow()

    ctx_key = f"{req.session_id}"
    ctx = _AGENT_CONTEXTS.get(ctx_key)
    if ctx is None:
        ctx = Context(workflow)
        _AGENT_CONTEXTS[ctx_key] = ctx
    message = f"""
    当前日期是：{date.today().isoformat()}
    用户问题：{req.question}
    """
    response = await workflow.run(
        user_msg=message, ctx=ctx
    )

    return QueryResponse(answer=str(response))