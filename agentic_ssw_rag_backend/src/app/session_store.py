from __future__ import annotations

import json
import logging
from functools import lru_cache
from typing import Any

import redis.asyncio as redis
from llama_index.core.workflow import Context
from workflows.context.serializers import JsonPickleSerializer

from app.config import get_settings


_CONTEXT_SERIALIZER = JsonPickleSerializer()
logger = logging.getLogger(__name__)


@lru_cache(maxsize=1)
def get_redis_client() -> redis.Redis:
    settings = get_settings()
    return redis.Redis(
        host=settings.redis_host,
        port=settings.redis_port,
        db=settings.redis_db,
        password=settings.redis_password or None,
        decode_responses=True,
    )


def _context_key(scope: str, session_id: str) -> str:
    settings = get_settings()
    return f"{settings.redis_session_key_prefix}:{scope}:{session_id}"


async def load_agent_context(workflow: Any, scope: str, session_id: str) -> Context:
    try:
        raw_context = await get_redis_client().get(_context_key(scope, session_id))
    except Exception:
        logger.exception("Failed to load agent context from Redis")
        return Context(workflow, serializer=_CONTEXT_SERIALIZER)

    if not raw_context:
        return Context(workflow, serializer=_CONTEXT_SERIALIZER)

    try:
        context_data = json.loads(raw_context)
        return Context.from_dict(
            workflow,
            context_data,
            serializer=_CONTEXT_SERIALIZER,
        )
    except Exception:
        logger.exception("Failed to deserialize agent context from Redis")
        return Context(workflow, serializer=_CONTEXT_SERIALIZER)


async def save_agent_context(scope: str, session_id: str, ctx: Context) -> None:
    try:
        settings = get_settings()
        context_data = ctx.to_dict(serializer=_CONTEXT_SERIALIZER)
        payload = json.dumps(context_data, ensure_ascii=False)
        key = _context_key(scope, session_id)

        if settings.redis_session_ttl_seconds > 0:
            await get_redis_client().set(
                key,
                payload,
                ex=settings.redis_session_ttl_seconds,
            )
            return

        await get_redis_client().set(key, payload)
    except Exception:
        logger.exception("Failed to save agent context to Redis")


async def close_redis_client() -> None:
    try:
        await get_redis_client().aclose()
    except RuntimeError:
        pass
    finally:
        get_redis_client.cache_clear()
