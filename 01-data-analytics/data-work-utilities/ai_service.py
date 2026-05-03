"""
Модуль для работы с AI API
Поддерживает GigaChat и OpenRouter агентов
Выполняет два анализа: сначала GigaChat, затем OpenRouter
"""
import os
import pathlib
import asyncio
import json
from typing import List, Dict, Any, Optional
from dotenv import load_dotenv
import aiohttp

# Импорты для GigaChat
try:
    from gigachat import GigaChat
    GIGACHAT_AVAILABLE = True
except ImportError:
    GIGACHAT_AVAILABLE = False

# Загружаем переменные окружения из .env файла
load_dotenv()

# Настройки GigaChat
GIGA_CREDENTIALS = os.getenv("GIGA_CREDENTIALS")
# Опция для отключения проверки SSL сертификатов (для разработки, не рекомендуется для продакшена)
GIGA_VERIFY_SSL = os.getenv("GIGA_VERIFY_SSL", "true").lower() in ("true", "1", "yes")

# Настройки OpenRouter
OPENROUTER_API_KEY = os.getenv("OPENROUTER_API_KEY")
OPENROUTER_API_URL = os.getenv("OPENROUTER_API_URL", "https://openrouter.ai/api/v1/chat/completions")
# Модель опциональна - если не указана, будет использована модель из профиля API (если поддерживается)
OPENROUTER_MODEL = os.getenv("OPENROUTER_MODEL", "")


class BaseAIAgent:
    """Базовый класс для AI-агентов"""
    
    async def send_request(self, system_prompt: str, user_prompt: str) -> str:
        """Отправляет запрос к AI и возвращает ответ"""
        raise NotImplementedError


class GigaChatAgent(BaseAIAgent):
    """Агент для работы с GigaChat API"""
    
    def __init__(self):
        if not GIGACHAT_AVAILABLE:
            raise ImportError("Библиотека gigachat не установлена. Установите: pip install gigachat")
        
        if not GIGA_CREDENTIALS:
            raise ValueError("GIGA_CREDENTIALS не установлен в переменных окружения (.env файл)")
        
        self.credentials = GIGA_CREDENTIALS
        self._prepare_environment()
    
    def _prepare_environment(self):
        """Подготавливает окружение для GigaChat (сертификаты и т.д.)"""
        # Настройка сертификатов (если есть)
        current = pathlib.Path(__file__).resolve().parent
        ca_bundle = current / "certs" / "ca-bundle.pem"
        
        # Если ca-bundle.pem не существует, создаём его из всех .cer файлов
        if not ca_bundle.exists():
            certs_dir = ca_bundle.parent
            if certs_dir.exists():
                cer_files = list(certs_dir.glob("*.cer"))
                if cer_files:
                    try:
                        # Создаем ca-bundle.pem из .cer файлов
                        with open(ca_bundle, 'w', encoding='utf-8') as pem_file:
                            for cer_file in cer_files:
                                try:
                                    # Пробуем прочитать как текстовый файл (UTF-8)
                                    with open(cer_file, 'r', encoding='utf-8') as cf:
                                        content = cf.read()
                                        pem_file.write(content + '\n')
                                except (UnicodeDecodeError, UnicodeError):
                                    try:
                                        # Если не utf-8, пробуем ascii
                                        with open(cer_file, 'r', encoding='ascii') as cf:
                                            content = cf.read()
                                            pem_file.write(content + '\n')
                                    except (UnicodeDecodeError, UnicodeError):
                                        # Если текстовый формат не подходит, пропускаем этот файл
                                        continue
                    except Exception as e:
                        # Если не удалось создать, продолжаем без сертификатов
                        # Логируем ошибку, но не прерываем выполнение
                        import sys
                        print(f"Предупреждение: не удалось создать ca-bundle.pem: {e}", file=sys.stderr)
        
        # Устанавливаем переменные окружения для сертификатов
        # Если сертификат не найден, библиотека будет использовать системные сертификаты
        if ca_bundle.exists():
            os.environ["SSL_CERT_FILE"] = str(ca_bundle)
            os.environ["REQUESTS_CA_BUNDLE"] = str(ca_bundle)
    
    async def send_request(self, system_prompt: str, user_prompt: str) -> str:
        """Отправляет запрос к GigaChat API"""
        try:
            # Импортируем необходимые классы
            from gigachat.models import Chat, Messages
            from gigachat.models.messages_role import MessagesRole
            
            # Создаем клиент GigaChat
            # Используем настройку из переменных окружения для проверки SSL
            giga = GigaChat(credentials=self.credentials, verify_ssl_certs=GIGA_VERIFY_SSL)
            
            # Формируем сообщения в правильном формате
            messages = [
                Messages(role=MessagesRole.SYSTEM, content=system_prompt),
                Messages(role=MessagesRole.USER, content=user_prompt)
            ]
            
            # Создаем объект Chat
            chat_payload = Chat(
                messages=messages,
                temperature=0.7,
                max_tokens=2000
            )
            
            # Отправляем запрос (GigaChat использует синхронный API, но мы оборачиваем его)
            # Для асинхронной работы используем asyncio.to_thread
            response = await asyncio.to_thread(giga.chat, chat_payload)
            
            # Извлекаем текст ответа
            if hasattr(response, 'choices') and len(response.choices) > 0:
                return response.choices[0].message.content
            elif isinstance(response, dict):
                if "choices" in response and len(response["choices"]) > 0:
                    return response["choices"][0].get("message", {}).get("content", "")
            else:
                # Альтернативный способ извлечения
                if hasattr(response, 'content'):
                    return response.content
                elif isinstance(response, str):
                    return response
            
            raise Exception("Не удалось извлечь ответ от GigaChat")
            
        except Exception as e:
            raise Exception(f"Ошибка при отправке запроса к GigaChat: {str(e)}")


class OpenRouterAgent(BaseAIAgent):
    """Агент для работы с OpenRouter API"""
    
    def __init__(self):
        if not OPENROUTER_API_KEY:
            raise ValueError("OPENROUTER_API_KEY не установлен в переменных окружения (.env файл)")
        self.api_key = OPENROUTER_API_KEY
        self.api_url = OPENROUTER_API_URL
    
    async def send_request(self, system_prompt: str, user_prompt: str) -> str:
        """Отправляет запрос к OpenRouter API"""
        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json",
            "HTTP-Referer": os.getenv("OPENROUTER_HTTP_REFERER", ""),
            "X-Title": os.getenv("OPENROUTER_X_TITLE", "Data Analyzer")
        }
        
        # Формируем payload
        # Поле model обязательно для OpenRouter API
        payload = {
            "model": OPENROUTER_MODEL if OPENROUTER_MODEL else "deepseek/deepseek-r1-0528",
            "messages": [
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_prompt}
            ],
            "temperature": 0.7,
            "max_tokens": 2000
        }
        
        async with aiohttp.ClientSession() as session:
            try:
                async with session.post(self.api_url, headers=headers, json=payload) as response:
                    if response.status != 200:
                        error_text = await response.text()
                        # Пытаемся распарсить JSON ошибки для более подробного сообщения
                        try:
                            error_json = json.loads(error_text)
                            error_msg = error_json.get("error", {}).get("message", error_text)
                            error_code = error_json.get("error", {}).get("code", response.status)
                            raise Exception(f"Ошибка OpenRouter API ({error_code}): {error_msg}")
                        except (json.JSONDecodeError, ValueError):
                            raise Exception(f"Ошибка OpenRouter API: {response.status} - {error_text}")
                    
                    data = await response.json()
                    
                    # Извлекаем текст ответа
                    if "choices" in data and len(data["choices"]) > 0:
                        message = data["choices"][0].get("message", {})
                        content = message.get("content", "")
                        return content
                    else:
                        raise Exception("Неожиданный формат ответа от OpenRouter API")
            
            except aiohttp.ClientError as e:
                raise Exception(f"Ошибка при отправке запроса к OpenRouter: {str(e)}")


def get_agent() -> GigaChatAgent:
    """
    Создает и возвращает GigaChat агент
    
    Returns:
        GigaChatAgent: Экземпляр агента GigaChat
    """
    return GigaChatAgent()


async def analyze_table_data(
    headers: List[str], 
    rows: List[Dict[str, Any]], 
    max_rows: int = 50
) -> Dict[str, str]:
    """
    Отправляет первые N строк таблицы в AI для анализа (GigaChat и OpenRouter)
    
    Args:
        headers: Список заголовков столбцов
        rows: Список строк данных (словари)
        max_rows: Максимальное количество строк для отправки (по умолчанию 50)
    
    Returns:
        Dict[str, str]: Словарь с анализами от обоих агентов {"gigachat": "...", "openrouter": "..."}
    """
    # Берем первые max_rows строк
    data_rows = rows[:max_rows]
    
    # Формируем текстовое представление таблицы
    table_text = format_table_for_ai(headers, data_rows)
    
    # Формируем системный промпт
    system_prompt = """Ты - аналитическая система с большим опытом. Твоя задача - анализировать табличные данные, делать выводы и находить аномалии или интересные тенденции."""
    
    user_prompt = f"""Вот первые {len(data_rows)} строк таблицы:

{table_text}"""
    
    results = {}
    
    # Первый анализ - GigaChat
    try:
        gigachat_agent = GigaChatAgent()
        gigachat_result = await gigachat_agent.send_request(system_prompt, user_prompt)
        results["gigachat"] = gigachat_result
    except Exception as e:
        results["gigachat"] = f"Ошибка: {str(e)}"
    
    # Второй анализ - OpenRouter
    try:
        openrouter_agent = OpenRouterAgent()
        openrouter_result = await openrouter_agent.send_request(system_prompt, user_prompt)
        results["openrouter"] = openrouter_result
    except Exception as e:
        results["openrouter"] = f"Ошибка: {str(e)}"
    
    return results


def format_table_for_ai(headers: List[str], rows: List[Dict[str, Any]]) -> str:
    """
    Форматирует таблицу в текстовый вид для отправки в AI
    
    Args:
        headers: Список заголовков
        rows: Список строк данных
    
    Returns:
        str: Отформатированный текст таблицы
    """
    # Создаем текстовое представление таблицы
    table_lines = []
    
    # Заголовки
    header_line = " | ".join(str(h) for h in headers)
    table_lines.append(header_line)
    table_lines.append("-" * len(header_line))
    
    # Строки данных
    for row in rows:
        row_values = []
        for header in headers:
            value = row.get(header, "")
            # Преобразуем значение в строку, обрабатывая None
            if value is None:
                value_str = ""
            else:
                value_str = str(value)
            row_values.append(value_str)
        row_line = " | ".join(row_values)
        table_lines.append(row_line)
    
    return "\n".join(table_lines)
