from langchain_google_genai import ChatGoogleGenerativeAI
from langchain_openai import ChatOpenAI
from app.config import get_settings

def get_llm():
    """Returns the configured LLM client dynamically based on Settings."""
    settings = get_settings()
    provider = settings.llm_provider.lower().strip()
    
    if provider == "openai":
        if not settings.openai_api_key:
            raise ValueError("openai_api_key is not configured in settings/env but llm_provider is set to 'openai'")
        return ChatOpenAI(
            model="gpt-4o-mini",
            api_key=settings.openai_api_key,
            temperature=0.3,
        )
    elif provider == "gemini":
        if not settings.gemini_api_key:
            raise ValueError("gemini_api_key is not configured in settings/env but llm_provider is set to 'gemini'")
        return ChatGoogleGenerativeAI(
            model=settings.llm_model,
            google_api_key=settings.gemini_api_key,
            temperature=0.3,
        )
    else:
        raise ValueError(f"Unsupported LLM provider: {settings.llm_provider}")
