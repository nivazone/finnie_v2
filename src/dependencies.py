from langchain_openai import ChatOpenAI
from pydantic import SecretStr
from config import get_settings
from functools import lru_cache
from psycopg_pool import AsyncConnectionPool
from search_providers import TavilySearchClient, SerperSearchClient, SearchProvider
from langchain.callbacks.streaming_stdout import StreamingStdOutCallbackHandler

@lru_cache(maxsize=1)
def get_llm(
    streaming: bool = False,
    callbacks: list | None = None,
) -> ChatOpenAI:
    s = get_settings()

    return ChatOpenAI(
        model=s.MODEL_NAME,
        base_url=s.OPENAI_BASE_URL,
        api_key=s.OPENAI_API_KEY or None,
        temperature=0,
        streaming=streaming,
        callbacks=callbacks or ([] if not streaming else [StreamingStdOutCallbackHandler()]),
    )

@lru_cache(maxsize=1)
def get_financial_insights_llm() -> ChatOpenAI:
    s = get_settings()

    return ChatOpenAI(
        model=s.FINANCIAL_INSIGHTS_MODEL_NAME,
        base_url=s.OPENAI_BASE_URL,
        api_key=s.OPENAI_API_KEY or None,
        temperature=0,
    )




# def get_llm() -> ChatOpenAI:
#     s = get_settings()

#     return ChatOpenAI(
#         model=s.MODEL_NAME,
#         base_url=s.OPENAI_BASE_URL,
#         api_key=SecretStr(s.OPENAI_API_KEY) if s.OPENAI_API_KEY is not None else None,
#     )

@lru_cache(maxsize=1)
def get_text_parser_llm() -> ChatOpenAI:
    s = get_settings()

    return ChatOpenAI(
        model=s.PARSER_MODEL_NAME,
        base_url=s.OPENAI_BASE_URL,
        api_key=SecretStr(s.OPENAI_API_KEY) if s.OPENAI_API_KEY is not None else None,
    )

@lru_cache(maxsize=1)
def get_transaction_classifier_llm() -> ChatOpenAI:
    s = get_settings()

    return ChatOpenAI(
        model=s.PARSER_MODEL_NAME,
        base_url=s.OPENAI_BASE_URL,
        api_key=SecretStr(s.OPENAI_API_KEY) if s.OPENAI_API_KEY is not None else None,
    )

@lru_cache(maxsize=1)
def get_search_client() -> SearchProvider:
    s = get_settings()
    provider = (s.SEARCH_PROVIDER or "tavily").lower()

    if provider == "tavily":
        return TavilySearchClient(max_results=3)
    elif provider == "serper":
        return SerperSearchClient(max_results=3)
    else:
        raise ValueError(f"Unsupported search provider: {provider}")

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