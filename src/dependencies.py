from langchain_openai import ChatOpenAI
from config import get_settings

def get_llm() -> ChatOpenAI:
    s = get_settings()

    return ChatOpenAI(
        model=s.MODEL_NAME,
        base_url=s.OPENAI_BASE_URL,
        api_key=s.OPENAI_API_KEY,
    )