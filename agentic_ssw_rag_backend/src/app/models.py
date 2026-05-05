from typing import Optional, List
from pydantic import BaseModel, Field


class QueryRequest(BaseModel):
    question: str = Field(..., description="用户问题")
    access_tags: List[str] = Field(default_factory=list, description="查询条件")
    top_k: Optional[int] = Field(default=None, description="覆盖默认 top_k")


class ChatRequest(QueryRequest):
    question: str = Field(..., description="用户问题")
    session_id: str = Field(default="default", description="会话 ID，用于 Agent 记忆")
    access_tags: List[str] = Field(default_factory=list, description="查询条件")
    top_k: Optional[int] = Field(default=None, description="覆盖默认 top_k")

class SourceChunk(BaseModel):
    score: Optional[float] = None
    text: str
    metadata: dict


class QueryResponse(BaseModel):
    answer: str
    sources: List[SourceChunk] = Field(default_factory=list)
