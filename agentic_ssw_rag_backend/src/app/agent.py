from functools import lru_cache

from llama_index.core.agent import AgentWorkflow
from llama_index.core.agent.workflow import ReActAgent
from llama_index.core.tools import QueryEngineTool

from .Neo4jCompanyRepository import child_company_tool, company_jobs_tool
from .llm import build_llm, build_moonshot_llm
from .rag import build_query_engine


AGENT_SYSTEM_PROMPT = """你是技术文档 Agentic RAG 助手。

你拥有一个技术文档查询工具 document_kb。
行为规则：
1. 用户询mysql、redis、tcp、io、时，必须调用 document_kb。
2. 不要直接编造知识库中没有的内容。
3. 回答时给出清晰结论、依据、步骤和风险提示。
4. 如果证据不足，说明缺少哪些材料，并建议用户补充哪些文档。
"""

@lru_cache(maxsize=16)
def build_agent(
    access_tags: tuple[str] | None = None,
    top_k: int | None = None,
) -> ReActAgent:
    query_engine = build_query_engine(
        access_tags=list(access_tags) if access_tags else [],
        top_k=top_k,
    )

    kb_tool = QueryEngineTool.from_defaults(
        query_engine=query_engine,
        name="document_kb",
        description=("查询企业知识库，适合制度、政策、文档、FAQ、说明类问题。"),
    )

    return ReActAgent(
        name="RagAgent",
        tools=[kb_tool],
        description="查询企业知识库，适合制度、文档、政策、说明、FAQ 等非结构化知识。",
        llm=build_moonshot_llm(),
        system_prompt=AGENT_SYSTEM_PROMPT,
    )


@lru_cache(maxsize=1)
def build_graph_agent(
) -> ReActAgent:
    return ReActAgent(
        name="Neo4jAgent",
        tools=[child_company_tool, company_jobs_tool],
        description="查询 Neo4j 业务图数据库，适合公司关系、控股关系、岗位数量、企业统计等结构化数据查询。",
        system_prompt="""
        你是 Neo4j 业务数据 Agent。
        只能使用 Neo4j 工具查询业务数据。
        不要回答知识库、政策、制度类问题。
        """,
        llm=build_moonshot_llm()
    )


@lru_cache(maxsize=1)
def build_router_agent(
) -> ReActAgent:
    return ReActAgent(
    name="RouterAgent",
    description="根据用户问题判断调用 Neo4jAgent 还是 RagAgent。",
    system_prompt="""
    你是主路由 Agent。
    路由规则：
    1. 公司关系、控股、子公司、岗位数量、统计、业务字段查询 => 交给 Neo4jAgent
    2. 制度、政策、文档、知识库、FAQ、说明解释 => 交给 RagAgent
    3. 如果两个都需要，分别交给两个 Agent，再综合回答。
    """,
    llm=build_moonshot_llm(),
    tools=[],
    can_handoff_to=["Neo4jAgent", "RagAgent"],
)
@lru_cache(maxsize=1)
def build_agent_workflow(
) -> AgentWorkflow:
    return AgentWorkflow(
    agents=[build_router_agent(), build_agent(), build_graph_agent()],
    root_agent="RouterAgent",
  )
