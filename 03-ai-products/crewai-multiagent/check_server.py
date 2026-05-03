"""
Диагностический скрипт для проверки готовности сервера к запуску.
Запустите: python check_server.py
"""
import sys
import os

def check_dependencies():
    """Проверка установленных зависимостей."""
    print("=" * 60)
    print("Проверка зависимостей...")
    print("=" * 60)
    
    required = {
        "fastapi": "FastAPI",
        "uvicorn": "Uvicorn",
        "crewai": "CrewAI",
        "dotenv": "python-dotenv",
    }
    
    missing = []
    for module, name in required.items():
        try:
            if module == "dotenv":
                import dotenv
                print(f"✓ {name} установлен")
            else:
                mod = __import__(module)
                version = getattr(mod, "__version__", "unknown")
                print(f"✓ {name} установлен (версия: {version})")
        except ImportError:
            print(f"✗ {name} НЕ установлен")
            missing.append(name)
    
    if missing:
        print(f"\n✗ Отсутствуют: {', '.join(missing)}")
        print("Установите: pip install -r requirements.txt")
        return False
    
    print("\n✓ Все зависимости установлены")
    return True


def check_files():
    """Проверка наличия необходимых файлов."""
    print("\n" + "=" * 60)
    print("Проверка файлов...")
    print("=" * 60)
    
    required_files = [
        "api.py",
        "seo_crew.py",
        "agents.py",
        "tasks/__init__.py",
        "tasks/task_parse.py",
        "tasks/task_analyze.py",
        "tasks/task_recommend.py",
        ".env",
    ]
    
    missing = []
    for file in required_files:
        if os.path.exists(file):
            print(f"✓ {file} существует")
        else:
            print(f"✗ {file} НЕ найден")
            missing.append(file)
    
    if missing:
        print(f"\n✗ Отсутствуют файлы: {', '.join(missing)}")
        if ".env" in missing:
            print("Создайте .env из .env.example")
        return False
    
    print("\n✓ Все необходимые файлы присутствуют")
    return True


def check_imports():
    """Проверка импортов."""
    print("\n" + "=" * 60)
    print("Проверка импортов...")
    print("=" * 60)
    
    try:
        print("Проверка импорта FastAPI...")
        from fastapi import FastAPI
        print("✓ FastAPI импортирован")
    except Exception as e:
        print(f"✗ Ошибка импорта FastAPI: {e}")
        return False
    
    try:
        print("Проверка импорта seo_crew...")
        from seo_crew import run_seo_analysis
        print("✓ seo_crew импортирован")
    except ImportError as e:
        print(f"✗ Ошибка импорта seo_crew: {e}")
        import traceback
        traceback.print_exc()
        return False
    except Exception as e:
        print(f"✗ Ошибка при импорте seo_crew: {e}")
        import traceback
        traceback.print_exc()
        return False
    
    try:
        print("Проверка импорта agents...")
        from agents import reader, analyst, core_engineer
        print("✓ agents импортированы")
    except Exception as e:
        print(f"✗ Ошибка импорта agents: {e}")
        import traceback
        traceback.print_exc()
        return False
    
    try:
        print("Проверка импорта tasks...")
        from tasks import task_parse, task_analyze, task_recommend
        print("✓ tasks импортированы")
    except Exception as e:
        print(f"✗ Ошибка импорта tasks: {e}")
        import traceback
        traceback.print_exc()
        return False
    
    print("\n✓ Все импорты успешны")
    return True


def check_port():
    """Проверка доступности порта."""
    print("\n" + "=" * 60)
    print("Проверка порта 8001...")
    print("=" * 60)
    
    import socket
    
    sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    result = sock.connect_ex(('127.0.0.1', 8001))
    sock.close()
    
    if result == 0:
        print("⚠ Порт 8001 уже занят!")
        print("Остановите другой процесс или измените порт")
        return False
    else:
        print("✓ Порт 8001 свободен")
        return True


def main():
    """Основная функция диагностики."""
    print("\n" + "=" * 60)
    print("ДИАГНОСТИКА СЕРВЕРА SEO CREW API")
    print("=" * 60 + "\n")
    
    checks = [
        ("Зависимости", check_dependencies),
        ("Файлы", check_files),
        ("Импорты", check_imports),
        ("Порт", check_port),
    ]
    
    results = []
    for name, check_func in checks:
        try:
            result = check_func()
            results.append((name, result))
        except Exception as e:
            print(f"\n✗ Ошибка при проверке {name}: {e}")
            results.append((name, False))
    
    print("\n" + "=" * 60)
    print("ИТОГИ ПРОВЕРКИ")
    print("=" * 60)
    
    all_ok = True
    for name, result in results:
        status = "✓ ПРОЙДЕНА" if result else "✗ НЕ ПРОЙДЕНА"
        print(f"{name}: {status}")
        if not result:
            all_ok = False
    
    print("\n" + "=" * 60)
    if all_ok:
        print("✓ ВСЕ ПРОВЕРКИ ПРОЙДЕНЫ!")
        print("Сервер готов к запуску: python api.py")
    else:
        print("✗ ОБНАРУЖЕНЫ ПРОБЛЕМЫ")
        print("Исправьте ошибки перед запуском сервера")
    print("=" * 60 + "\n")
    
    return 0 if all_ok else 1


if __name__ == "__main__":
    sys.exit(main())
