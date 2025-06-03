"""bot/services/openrouter_client.py
OpenRouter client + вспомогательные функции для общения с LLM.
Здесь вызывается load_dotenv, поэтому ключ из .env доступен ещё до импорта
в других файлах.
"""

import os
import base64
import asyncio
import logging
from typing import Optional

from openai import OpenAI
from dotenv import load_dotenv

# -- Загрузим .env раньше, чем будем читать переменные окружения ---------
load_dotenv()  # гарантирует, что OPENROUTER_API_KEY доступен при импорте

logger = logging.getLogger(__name__)

# ---------------------- Инициализация клиента ---------------------------
OPENROUTER_API_KEY = os.getenv("OPENROUTER_API_KEY")
if not OPENROUTER_API_KEY:
    raise RuntimeError(
        "OPENROUTER_API_KEY не найден. Добавьте его в .env или переменные окружения."
    )

client = OpenAI(
    base_url="https://openrouter.ai/api/v1",
    api_key=OPENROUTER_API_KEY,
)


# ----------------------- Помощники для запросов -------------------------
async def ask_llm_with_text(text: str, model: str = "anthropic/claude-sonnet-4") -> str:
    """Отправить только текст и вернуть ответ."""
    logger.debug("LLM request (text only) | model=%s", model)
    response = await asyncio.to_thread(
        client.chat.completions.create,
        model=model,
        messages=[{"role": "user", "content": text}],
    )
    answer = response.choices[0].message.content.strip()
    logger.debug("LLM response length=%s chars", len(answer))
    return answer


async def ask_llm_with_image(
    img_bytes: bytes,
    caption: str = "",
    model: str = "anthropic/claude-sonnet-4",
) -> str:
    """Отправить изображение (JPEG/PNG) + опц. подпись, вернуть ответ."""
    logger.debug(
        "LLM request (image) | caption=%s | img_size=%s bytes | model=%s",
        bool(caption),
        len(img_bytes),
        model,
    )

    b64 = base64.b64encode(img_bytes).decode()

    content_blocks = []
    if caption:
        content_blocks.append({"type": "text", "text": caption})
    content_blocks.append(
        {
            "type": "image_url",
            "image_url": {"url": f"data:image/jpeg;base64,{b64}"},
        }
    )

    response = await asyncio.to_thread(
        client.chat.completions.create,
        model=model,
        messages=[{"role": "user", "content": content_blocks}],
    )
    answer = response.choices[0].message.content.strip()
    logger.debug("LLM response length=%s chars", len(answer))
    return answer


__all__ = [
    "client",
    "ask_llm_with_text",
    "ask_llm_with_image",
]
