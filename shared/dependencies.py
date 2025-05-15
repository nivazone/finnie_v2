from langchain_openai import ChatOpenAI
from psycopg import connect, Connection
import os

def get_llm() -> ChatOpenAI:
    return ChatOpenAI(
        model=os.getenv("OPENAI_MODEL", "gpt-4o"),
        base_url=os.getenv("OPENAI_BASE_URL", None),
        api_key=os.getenv("OPENAI_API_KEY", None),
        temperature=0
    )

def get_db_connection() -> Connection:
    return connect(
        host=os.getenv("POSTGRES_HOST", "localhost"),
        port=os.getenv("POSTGRES_PORT", "5432"),
        dbname=os.getenv("POSTGRES_DB"),
        user=os.getenv("POSTGRES_USER"),
        password=os.getenv("POSTGRES_PASSWORD"),
    )