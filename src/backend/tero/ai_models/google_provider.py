import io
from typing import Optional

from langchain_core.language_models.chat_models import BaseChatModel
from langchain_google_genai import ChatGoogleGenerativeAI

from ..core.env import env
from .domain import AiModelProvider


class GoogleProvider(AiModelProvider):

    def _build_chat_model(self, model: str, temperature: Optional[float], reasoning_effort: Optional[str], streaming: bool) -> BaseChatModel:
        google_model_id = env.google_model_id_mapping.get(model)    
        if not google_model_id:
            raise ValueError(f"Model {model} not supported by Google")
        return ChatGoogleGenerativeAI(
            google_api_key=env.google_api_key,
            model=google_model_id,
            temperature=temperature)

    def supports_model(self, model: str) -> bool:
        return model in env.google_model_id_mapping

    async def transcribe_audio(self, file: io.BytesIO, model: str) -> str:
        raise NotImplementedError("Transcription is not supported by Google")
