import json
import requests
from bs4 import BeautifulSoup
from typing import Dict, List

from openai_template import ask_openai

def generate_future_prompts_from_url(url: str) -> Dict[str, List[str]]:
    # Fetch HTML content
    try:
        response = requests.get(url)
        response.raise_for_status()
        html_content = response.text
    except requests.RequestException as e:
        raise Exception(f"Failed to fetch URL content: {str(e)}")

    # Extract clean text using BeautifulSoup
    soup = BeautifulSoup(html_content, 'html.parser')
    clean_text = soup.get_text(separator=' ', strip=True)

    # Truncate text if too long (OpenAI has context limits)
    max_text_length = 3000
    if len(clean_text) > max_text_length:
        clean_text = clean_text[:max_text_length] + "..."

    # Create system prompt for generating agent prompts
    system_prompt = """Ты агент, который создает системные промпты для анализа веб-сайта.
    Твоя задача - создать 5-6 системных промптов для ИИ-агентов, которые будут анализировать веб-сайт и генерировать целевой рекламный контент.
    
    Убедись, что промпты покрывают:
    1. Анализ целевой аудитории
    2. Преимущества продукта/услуги
    3. Уникальные торговые предложения
    4. Анализ тона и стиля
    5. Генерация рекламных текстов
    
    Верни промпты в формате JSON:
    {
    "prompts": [
        "Ты агент, который...",
        "Ты агент, отвечающий за...",
    ]
    }"""

    # Get response from OpenAI
    try:
        response = ask_openai(system_prompt=system_prompt, user_message=clean_text, response_format=True)
        # Parse the response as JSON
        result = json.loads(response)
        return result
    except json.JSONDecodeError:
        raise Exception(f"Failed to parse OpenAI response as JSON: {response}")
    except Exception as e:
        raise Exception(f"Error while getting OpenAI response: {str(e)}")

def query_with_custom_system_prompt(prompt: str, content: str) -> str:
    """
    Генерирует ответ, используя пользовательский системный промпт и предоставленный контент.
    
    Args:
        prompt (str): Пользовательский системный промпт, определяющий роль и поведение агента
        content (str): Контент для анализа или генерации на его основе
        
    Returns:
        str: Сгенерированный ответ от модели
    """
    try:
        response = ask_openai(system_prompt=prompt, user_message=content)
        return response
    except Exception as e:
        raise Exception(f"Error while getting OpenAI response: {str(e)}")

def generate_final_ad_post(all_results: List[str]) -> str:
    """
    Генерирует финальный рекламный пост на основе результатов работы всех агентов.
    
    Args:
        all_results (List[str]): Список результатов от всех предыдущих агентов
        
    Returns:
        str: Готовый текст рекламного поста
    """
    # Объединяем все результаты в один текст
    combined_results = "\n\n=== Результат анализа ===\n\n".join(all_results)
    
    # Формируем системный промпт для финального агента
    system_prompt = """Ты агент, который составляет рекламный пост по результатам анализа.
    Твоя задача - создать привлекательный и эффективный рекламный текст на основе выводов предыдущих агентов.

    Используй предоставленную информацию для создания поста, который:
    - Привлекает внимание целевой аудитории
    - Подчеркивает ключевые преимущества продукта/услуги
    - Содержит четкий призыв к действию
    - Использует подходящий тон и стиль"""

    # Получаем ответ от OpenAI
    try:
        response = ask_openai(system_prompt=system_prompt, user_message=combined_results)
        return response
    except Exception as e:
        raise Exception(f"Ошибка при получении ответа от OpenAI: {str(e)}") 