#!/usr/bin/env python3
"""
Скрипт для проверки настройки Yandex Wordstat MCP
"""

import os
import sys
from pathlib import Path

def check_env_file():
    """Проверка наличия файла .env"""
    env_path = Path(".env")
    if not env_path.exists():
        print("❌ Файл .env не найден!")
        print("   Создайте его командой: copy .env.example .env")
        return False
    print("✓ Файл .env найден")
    return True

def check_token():
    """Проверка наличия токена"""
    try:
        from dotenv import load_dotenv
        load_dotenv()
        
        token = os.getenv("WORDSTAT_TOKEN")
        if not token:
            print("❌ WORDSTAT_TOKEN не установлен в .env")
            return False
        
        if token == "ВАШ_OAUTH_ТОКЕН_ОТ_ЯНДЕКСА":
            print("❌ WORDSTAT_TOKEN не заменен на реальный токен")
            print("   Откройте .env и замените значение токена")
            return False
        
        if not token.startswith("y0_Ag"):
            print("⚠️  Токен не начинается с 'y0_Ag' - проверьте правильность")
        
        print(f"✓ Токен найден: {token[:20]}...")
        return True
    except ImportError:
        print("❌ python-dotenv не установлен")
        print("   Установите: pip install python-dotenv")
        return False

def check_dependencies():
    """Проверка установленных зависимостей"""
    required = [
        "fastapi",
        "uvicorn",
        "fastapi_mcp",
        "python_dotenv",
        "requests",
        "pydantic"
    ]
    
    missing = []
    for package in required:
        try:
            __import__(package.replace("-", "_"))
            print(f"✓ {package} установлен")
        except ImportError:
            print(f"❌ {package} не установлен")
            missing.append(package)
    
    if missing:
        print(f"\n⚠️  Установите недостающие пакеты:")
        print(f"   pip install {' '.join(missing)}")
        return False
    
    return True

def check_api_connection():
    """Проверка подключения к API"""
    try:
        from dotenv import load_dotenv
        import requests
        load_dotenv()
        
        token = os.getenv("WORDSTAT_TOKEN")
        if not token or token == "ВАШ_OAUTH_ТОКЕН_ОТ_ЯНДЕКСА":
            print("⚠️  Пропущена проверка подключения (токен не настроен)")
            return True
        
        headers = {
            "Content-Type": "application/json;charset=utf-8",
            "Authorization": f"Bearer {token}",
        }
        
        # Проверка через userInfo (не расходует квоту)
        url = "https://api.wordstat.yandex.net/v1/userInfo"
        response = requests.post(url, headers=headers, json={}, timeout=10)
        
        if response.status_code == 200:
            data = response.json()
            print("✓ Подключение к API успешно!")
            print(f"  Запросов в секунду: {data.get('requestsPerSecond', 'N/A')}")
            print(f"  Запросов в день: {data.get('requestsPerDay', 'N/A')}")
            print(f"  Осталось запросов: {data.get('remainingRequests', 'N/A')}")
            return True
        elif response.status_code == 401:
            print("❌ Ошибка авторизации (401)")
            print("   Проверьте правильность токена")
            return False
        elif response.status_code == 403:
            print("❌ Доступ запрещен (403)")
            print("   Убедитесь, что:")
            print("   - API Wordstat включен в Yandex Cloud")
            print("   - Заявка на доступ к API одобрена")
            return False
        else:
            print(f"⚠️  Неожиданный ответ API: {response.status_code}")
            print(f"   Ответ: {response.text[:200]}")
            return False
            
    except requests.exceptions.RequestException as e:
        print(f"⚠️  Ошибка подключения: {e}")
        print("   Проверьте интернет-соединение")
        return False
    except Exception as e:
        print(f"⚠️  Ошибка при проверке: {e}")
        return False

def main():
    print("=" * 50)
    print("Проверка настройки Yandex Wordstat MCP")
    print("=" * 50)
    print()
    
    checks = [
        ("Файл .env", check_env_file),
        ("Токен", check_token),
        ("Зависимости", check_dependencies),
        ("Подключение к API", check_api_connection),
    ]
    
    results = []
    for name, check_func in checks:
        print(f"\n[{name}]")
        try:
            result = check_func()
            results.append(result)
        except Exception as e:
            print(f"❌ Ошибка: {e}")
            results.append(False)
    
    print("\n" + "=" * 50)
    if all(results):
        print("✓ Все проверки пройдены! Сервер готов к работе.")
        return 0
    else:
        print("⚠️  Некоторые проверки не пройдены.")
        print("   См. инструкцию в SETUP_GUIDE.md")
        return 1

if __name__ == "__main__":
    sys.exit(main())
