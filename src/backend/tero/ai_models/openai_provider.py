import io
from typing import Optional, cast

from langchain_openai import ChatOpenAI
from langchain_core.language_models.chat_models import BaseChatModel
from openai import AsyncOpenAI
from pydantic import SecretStr

from ..core.env import env
from .domain import AiModelProvider


class OpenAIProvider(AiModelProvider):

    def _build_chat_model(self, model: str, temperature: Optional[float], reasoning_effort: Optional[str], streaming: bool) -> BaseChatModel:
        openai_model_id = env.openai_model_id_mapping[model]
        return ChatOpenAI(
            api_key=env.openai_api_key,
            model=openai_model_id,
            temperature=temperature,
            streaming=streaming)

    def supports_model(self, model: str) -> bool:
        return model in env.openai_model_id_mapping

    async def transcribe_audio(self, file: io.BytesIO, model: str) -> str:
        client = AsyncOpenAI(api_key=cast(SecretStr, env.openai_api_key).get_secret_value())
        response = await client.audio.transcriptions.create(
            file=file,
            model=env.openai_model_id_mapping[model]
        )
        return response.text
