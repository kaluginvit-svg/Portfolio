import asyncio
import logging
import sys

try:
    from app.services import call_openrouter_api
except ModuleNotFoundError as exc:
    missing = getattr(exc, "name", "")
    if missing == "aiohttp":
        print("❌ Не установлены зависимости. Установите их командой:")
        print("pip install -r requirements.txt")
        raise SystemExit(1) from exc
    raise


async def main() -> int:
    logging.basicConfig(level=logging.INFO)
    logger = logging.getLogger(__name__)

    prompt = " ".join(sys.argv[1:]).strip() if len(sys.argv) > 1 else "Привет! Как дела?"
    if not prompt:
        prompt = "Привет! Как дела?"

    logger.info("🧪 Тестовый запрос: %s", prompt)
    response = await call_openrouter_api(prompt)
    if not response:
        print("❌ Не удалось получить ответ от OpenRouter.")
        return 1

    print("✅ Ответ от OpenRouter:")
    print(response)
    return 0


if __name__ == "__main__":
    raise SystemExit(asyncio.run(main()))
