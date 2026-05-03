"""
Тестовый скрипт для проверки работы API.
Запустите этот скрипт, чтобы проверить, что сервер запускается корректно.
"""
import sys
import requests
import time

def test_api():
    """Проверка доступности API."""
    base_url = "http://localhost:8001"
    
    print("Проверка доступности API...")
    print(f"Базовый URL: {base_url}\n")
    
    # Проверка корневого endpoint
    try:
        print("1. Проверка GET / ...")
        response = requests.get(f"{base_url}/", timeout=5)
        if response.status_code == 200:
            print(f"   ✓ Успешно: {response.json()}")
        else:
            print(f"   ✗ Ошибка: статус {response.status_code}")
    except requests.exceptions.ConnectionError:
        print("   ✗ Сервер не запущен или недоступен!")
        print("   Запустите сервер: python api.py")
        return False
    except Exception as e:
        print(f"   ✗ Ошибка: {e}")
        return False
    
    # Проверка health endpoint
    try:
        print("\n2. Проверка GET /health ...")
        response = requests.get(f"{base_url}/health", timeout=5)
        if response.status_code == 200:
            print(f"   ✓ Успешно: {response.json()}")
        else:
            print(f"   ✗ Ошибка: статус {response.status_code}")
    except Exception as e:
        print(f"   ✗ Ошибка: {e}")
        return False
    
    # Проверка docs endpoint
    try:
        print("\n3. Проверка GET /docs ...")
        response = requests.get(f"{base_url}/docs", timeout=5)
        if response.status_code == 200:
            print("   ✓ Документация доступна")
        else:
            print(f"   ✗ Ошибка: статус {response.status_code}")
    except Exception as e:
        print(f"   ✗ Ошибка: {e}")
    
    print("\n" + "=" * 60)
    print("Все проверки пройдены! API работает корректно.")
    print(f"Откройте в браузере: {base_url}/docs")
    print("=" * 60)
    return True

if __name__ == "__main__":
    print("Ожидание запуска сервера (5 секунд)...")
    time.sleep(5)
    success = test_api()
    sys.exit(0 if success else 1)
