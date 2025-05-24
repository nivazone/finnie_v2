from langchain_openai import ChatOpenAI
from psycopg import connect, Connection
from langchain_tavily import TavilySearch
from typing import Optional, Any
from config import get_settings
from functools import lru_cache
from psycopg_pool import AsyncConnectionPool

def get_llm() -> ChatOpenAI:
    s = get_settings()

    return ChatOpenAI(
        model=s.MODEL_NAME,
        base_url=s.OPENAI_BASE_URL,
        api_key=s.OPENAI_API_KEY,
    )

def get_text_parser_llm() -> ChatOpenAI:
    s = get_settings()

    return ChatOpenAI(
        model=s.PARSER_MODEL_NAME,
        base_url=s.OPENAI_BASE_URL,
        api_key=s.OPENAI_API_KEY,
    )

def get_transaction_classifier_llm() -> ChatOpenAI:
    s = get_settings()

    return ChatOpenAI(
        model=s.PARSER_MODEL_NAME,
        base_url=s.OPENAI_BASE_URL,
        api_key=s.OPENAI_API_KEY,
    )

def get_search_client() -> TavilySearch:
    client = TavilySearch(max_results=3)
    return client

# -----------------------------
# Async DB Pool
# -----------------------------

_pool: AsyncConnectionPool | None = None

def get_db_pool() -> AsyncConnectionPool:
    if _pool is None:
        raise RuntimeError("DB pool not initialized. Call init_db_pool() first.")
    return _pool

async def init_db_pool():
    global _pool
    
    if _pool is None:
        s = get_settings()
        _pool = AsyncConnectionPool(
            conninfo=f"host={s.POSTGRES_HOST} port={s.POSTGRES_PORT} dbname={s.POSTGRES_DB} user={s.POSTGRES_USER} password={s.POSTGRES_PASSWORD}",
            max_size=10,
            timeout=10,
            open=False
        )
        await _pool.open()

async def close_db_pool():
    global _pool
    if _pool is not None:
        await _pool.close()
        _pool = None