from langchain_openai import ChatOpenAI
from psycopg import connect, Connection
from langchain_tavily import TavilySearch
from config import get_settings

def get_llm() -> ChatOpenAI:
    s = get_settings()

    return ChatOpenAI(
        model=s.MODEL_NAME,
        base_url=s.OPENAI_BASE_URL,
        api_key=s.OPENAI_API_KEY,
    )

def get_db_connection() -> Connection:
    s = get_settings()

    return connect(
        host=s.POSTGRES_HOST,
        port=s.POSTGRES_PORT,
        dbname=s.POSTGRES_DB,
        user=s.POSTGRES_USER,
        password=s.POSTGRES_PASSWORD,
    )

def get_search_client() -> TavilySearch:
    client = TavilySearch(max_results=3)
    return client