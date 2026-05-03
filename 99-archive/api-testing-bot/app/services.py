import logging
import asyncio
import json
from typing import Optional

import aiohttp

logger = logging.getLogger(__name__)


async def call_openrouter_api(user_message: str) -> Optional[str]:
	"""Отправить запрос к OpenRouter API и получить ответ"""
	from app.config import OPENROUTER_API_KEY, OPENROUTER_API_URL
	
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
				timeout=aiohttp.ClientTimeout(total=45)
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


async def call_chutes_api(user_message: str) -> Optional[str]:
	"""Отправить запрос к Chutes API и получить ответ"""
	from app.config import CHUTES_API_TOKEN
	
	if not CHUTES_API_TOKEN:
		logger.error("❌ CHUTES_API_TOKEN не установлен в переменных окружения")
		return None
	
	headers = {
		"Authorization": f"Bearer {CHUTES_API_TOKEN}",
		"Content-Type": "application/json"
	}
	
	body = {
		"model": "Qwen/Qwen3-32B",
		"messages": [
			{
				"role": "user",
				"content": user_message
			}
		],
		"stream": False,
		"max_tokens": 2048,
		"temperature": 0.7
	}
	
	try:
		logger.info(f"📤 Отправка запроса к Chutes API...")
		
		async with aiohttp.ClientSession() as session:
			async with session.post(
				"https://llm.chutes.ai/v1/chat/completions",
				headers=headers,
				json=body,
				timeout=aiohttp.ClientTimeout(total=45)
			) as resp:
				logger.info(f"📥 Ответ Chutes: {resp.status}")
				
				response_text = await resp.text()
				
				if resp.status == 200:
					try:
						data = json.loads(response_text)
						
						# Извлечение ответа из структуры Chutes
						if "choices" in data and len(data["choices"]) > 0:
							message_content = data["choices"][0].get("message", {}).get("content")
							if message_content:
								logger.info(f"✅ Получен ответ от Chutes ({len(message_content)} символов)")
								return message_content
							else:
								logger.warning("❌ Содержимое сообщения пусто в ответе API")
								return None
						else:
							logger.warning(f"❌ Структура ответа неправильная")
							return None
					except json.JSONDecodeError as e:
						logger.error(f"❌ Ошибка парсинга JSON: {e}\nОтвет: {response_text[:500]}")
						return None
				else:
					logger.error(f"❌ Chutes API error: HTTP {resp.status}")
					logger.error(f"📝 Ответ сервера: {response_text[:500]}")
					
					if resp.status == 401:
						logger.error("❌ Неверный API ключ Chutes")
					elif resp.status == 500:
						logger.error("❌ Сервер Chutes недоступен")
					
					return None
					
	except asyncio.TimeoutError:
		logger.error("❌ Timeout при запросе к Chutes API (более 45 секунд)")
		return None
	except aiohttp.ClientError as e:
		logger.error(f"❌ Сетевая ошибка при подключении к Chutes: {e}")
		return None
	except Exception as exc:
		logger.exception(f"❌ Неожиданная ошибка при вызове Chutes API: {exc}")
		return None


async def call_gigachat_api(user_message: str) -> Optional[str]:
	"""Отправить запрос к GigaChat API и получить ответ"""
	import os
	from app.gigachat_token import prepare_gigachat_env
	from gigachat import GigaChat
	
	def _send_sync() -> Optional[str]:
		credentials = prepare_gigachat_env()
		if not credentials:
			raise ValueError("GIGA_CREDENTIALS not found")
		
		with GigaChat(credentials=credentials, verify_ssl_certs=True) as giga:
			resp = giga.chat({
				"model": "GigaChat",
				"messages": [{"role": "user", "content": user_message}],
				"temperature": 0.7,
				"max_tokens": 1024,
			})
			
			if resp and resp.choices:
				choice = resp.choices[0].message
				if isinstance(choice, dict):
					return choice.get("content")
				return getattr(choice, "content", None)
			return None
	
	try:
		logger.info("📤 Отправка запроса к GigaChat...")
		result = await asyncio.to_thread(_send_sync)
		if result:
			logger.info(f"✅ Получен ответ от GigaChat ({len(result)} символов)")
		else:
			logger.warning("❌ Пустой ответ от GigaChat")
		return result
	except Exception as exc:
		logger.exception(f"❌ Ошибка при вызове GigaChat API: {exc}")
		return None


async def call_ai_api(user_message: str, agent: str = "openrouter") -> Optional[str]:
	"""Универсальная функция для вызова выбранного AI агента"""
	if agent.lower() == "chutes":
		return await call_chutes_api(user_message)
	if agent.lower() == "gigachat":
		return await call_gigachat_api(user_message)
	else:
		return await call_openrouter_api(user_message)
