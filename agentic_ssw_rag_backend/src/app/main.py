
from datetime import date

from fastapi import Depends, FastAPI, APIRouter
from app.agent import build_agent, build_graph_agent, build_agent_workflow
from app.BizException import register_exception_handlers
from app.config import get_settings
from app.documents import router as documents_router
from app.models import ChatRequest, QueryRequest, QueryResponse, SourceChunk
from app.rag import query_knowledge_base
from app.security import verify_api_key
from app.session_store import close_redis_client, load_agent_context, save_agent_context


router = APIRouter(
    prefix="/agent",
    dependencies=[Depends(verify_api_key)]
)
settings=get_settings()
def create_app() -> FastAPI:
    app = FastAPI()
    register_exception_handlers(app)
    app.include_router(router)
    app.include_router(documents_router)

    return app


app = create_app()


@app.on_event("shutdown")
async def shutdown_event():
    await close_redis_client()






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
        access_tags=tuple(req.access_tags),
        top_k=req.top_k,
    )

    ctx = await load_agent_context(agent, "chat", req.session_id)

    handler = agent.run(req.question, ctx=ctx)
    response = await handler
    await save_agent_context("chat", req.session_id, ctx)


    return QueryResponse(answer=str(response))



@app.post("/agent/graph", response_model=QueryResponse)
async def agent_graph(req: ChatRequest):
    # 根据租户 / 权限构建 agent。
    # 注意：如果每次请求都 build agent，会重复加载模型；生产环境建议做 agent / query_engine 缓存。
    agent = build_graph_agent()

    ctx = await load_agent_context(agent, "graph", req.session_id)
    message = f"""
    当前日期是：{date.today().isoformat()}
    用户问题：{req.question}
    """
    handler = agent.run(message, ctx=ctx)
    response = await handler
    await save_agent_context("graph", req.session_id, ctx)


    return QueryResponse(answer=str(response))


@app.post("/agent/search", response_model=QueryResponse)
async def agent_search(req: ChatRequest):
    # 根据租户 / 权限构建 agent。
    # 注意：如果每次请求都 build agent，会重复加载模型；生产环境建议做 agent / query_engine 缓存。
    workflow = build_agent_workflow()

    ctx = await load_agent_context(workflow, "search", req.session_id)
    message = f"""
    当前日期是：{date.today().isoformat()}
    用户问题：{req.question}
    """
    response = await workflow.run(
        user_msg=message, ctx=ctx
    )
    await save_agent_context("search", req.session_id, ctx)

    return QueryResponse(answer=str(response))
