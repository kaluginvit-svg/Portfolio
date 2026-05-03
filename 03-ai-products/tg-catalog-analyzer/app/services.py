import logging
import asyncio
import json
from typing import Optional

import aiohttp

logger = logging.getLogger(__name__)


async def call_openrouter_api(user_message: str) -> Optional[str]:
	"""Отправить запрос к OpenRouter API и получить ответ"""
	from app.config import (
		OPENROUTER_API_KEY,
		OPENROUTER_API_URL,
		OPENROUTER_TIMEOUT_SECONDS,
	)
	
	if not OPENROUTER_API_KEY:
		logger.error("❌ OPENROUTER_API_KEY не установлен в переменных окружения")
		return None
	
	headers = {
		"Authorization": f"Bearer {OPENROUTER_API_KEY}",
		"Content-Type": "application/json",
		"HTTP-Referer": "https://github.com/",
		"X-Title": "Telegram AI Bot"
	}
	
	payload = {
		"model": "@preset/vitaliy",
		"messages": [
			{
				"role": "user",
				"content": user_message
			}
		]
	}
	
	try:
		logger.info(f"📤 Отправка запроса к OpenRouter API...")
		
		async with aiohttp.ClientSession() as session:
			async with session.post(
				OPENROUTER_API_URL, 
				headers=headers, 
				json=payload,
				timeout=aiohttp.ClientTimeout(total=OPENROUTER_TIMEOUT_SECONDS)
			) as resp:
				logger.info(f"📥 Ответ OpenRouter: {resp.status}")
				
				response_text = await resp.text()
				
				if resp.status == 200:
					try:
						data = json.loads(response_text)
						logger.debug(f"📋 Полный ответ API: {json.dumps(data, ensure_ascii=False)[:500]}")
						
						# Извлечение ответа из структуры OpenRouter
						if "choices" in data and len(data["choices"]) > 0:
							message_content = data["choices"][0].get("message", {}).get("content")
							if message_content:
								logger.info(f"✅ Получен ответ от OpenRouter ({len(message_content)} символов)")
								return message_content
							else:
								logger.warning("❌ Содержимое сообщения пусто в ответе API")
								return None
						else:
							logger.warning(f"❌ Структура ответа неправильная: {list(data.keys())}")
							return None
					except json.JSONDecodeError as e:
						logger.error(f"❌ Ошибка парсинга JSON: {e}\nОтвет: {response_text[:500]}")
						return None
				else:
					logger.error(f"❌ OpenRouter API error: HTTP {resp.status}")
					logger.error(f"📝 Ответ сервера: {response_text[:500]}")
					
					# Проверка на превышение лимита
					if resp.status == 429:
						logger.warning("⚠️ Достигнут лимит запросов к OpenRouter API")
					elif resp.status == 401:
						logger.error("❌ Неверный API ключ OpenRouter")
					elif resp.status == 500:
						logger.error("❌ Сервер OpenRouter недоступен")
					
					return None
					
	except asyncio.TimeoutError:
		logger.error("❌ Timeout при запросе к OpenRouter API (более 45 секунд)")
		return None
	except aiohttp.ClientError as e:
		logger.error(f"❌ Сетевая ошибка при подключении к OpenRouter: {e}")
		return None
	except Exception as exc:
		logger.exception(f"❌ Неожиданная ошибка при вызове OpenRouter API: {exc}")
		return None

async def call_ai_api(user_message: str) -> Optional[str]:
	"""Вызов OpenRouter API"""
	return await call_openrouter_api(user_message)
