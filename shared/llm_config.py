import os
from crewai import LLM


def _normalize_crewai_ollama_model(model_name: str) -> str:
    """CrewAI Ollama models should use 'ollama/<model>' format."""
    clean_name = (model_name or "").strip()
    if not clean_name:
        return clean_name
    if "/" in clean_name:
        return clean_name
    return f"ollama/{clean_name}"

def get_base_llms():
    """
    Centralized connection factory for models used across teams.
    Ensures identical initialization configurations.
    """
    OLLAMA_HOST = os.getenv("OLLAMA_BASE_URL", "http://localhost:11434")
    LOCAL_MODEL = _normalize_crewai_ollama_model(os.getenv("LOCAL_MODEL", "llama3"))
    LOCAL_MODEL_PLUS = _normalize_crewai_ollama_model(os.getenv("LOCAL_MODEL_PLUS", "llama3"))
    VISION_MODEL = _normalize_crewai_ollama_model(os.getenv("VISION_MODEL", "llava"))

    # Shared Ollama instances
    local_model_obj = LLM(
        model=LOCAL_MODEL,
        base_url=OLLAMA_HOST,
        temperature=0.2
    )

    local_model_plus_obj = LLM(
        model=LOCAL_MODEL_PLUS,
        base_url=OLLAMA_HOST,
        temperature=0.2
    )

    vision_model_obj = LLM(
        model=VISION_MODEL,
        base_url=OLLAMA_HOST
    )

    # Optional Gemini instance
    gemini_api_key = os.getenv("GEMINI_API_KEY")
    gemini_model = os.getenv("GEMINI_MODEL")
    gemini_obj = None

    if gemini_api_key and gemini_model:
        try:
            gemini_obj = LLM(
                model=gemini_model,
                temperature=0.0,
                api_key=gemini_api_key
            )
        except ImportError:
            pass

    return {
        "LOCAL_MODEL_OBJ": local_model_obj,
        "LOCAL_MODEL_PLUS_OBJ": local_model_plus_obj,
        "VISION_MODEL_OBJ": vision_model_obj,
        "GEMINI": gemini_obj
    }
