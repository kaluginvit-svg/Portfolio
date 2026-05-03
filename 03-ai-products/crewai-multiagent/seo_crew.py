"""
SEO Crew: мультиагентная цепочка задач.

Агенты в agents.py, задачи в пакете tasks/ (task_parse, task_analyze, task_recommend).
Запуск: python seo_crew.py [URL]
"""
import os
from datetime import datetime
from dotenv import load_dotenv

from crewai import Crew, Process

load_dotenv()

from agents import reader, analyst, core_engineer
from tasks import task_parse, task_analyze, task_recommend

crew = Crew(
    agents=[reader, analyst, core_engineer],
    tasks=[task_parse, task_analyze, task_recommend],
    process=Process.sequential,
    verbose=True,
    output_log_file="logs/seo_crew_output.log",  # логи выполнения в файл
)


def _sanitize_filename(url: str) -> str:
    """Очистка URL для использования в имени файла."""
    return url.replace("https://", "").replace("http://", "").replace("/", "_")[:50]


def save_result(result, url: str = None):
    """
    Сохранить уже выполненный результат Crew в файлы.
    
    Args:
        result: CrewOutput (результат crew.kickoff())
        url: URL страницы (если не указан, используется "unknown")
    """
    # Создание директорий
    os.makedirs("results", exist_ok=True)
    os.makedirs("logs", exist_ok=True)
    
    # Подготовка данных
    url = url or "unknown"
    safe_url = _sanitize_filename(url)
    timestamp = datetime.now()
    timestamp_str = timestamp.strftime("%Y%m%d_%H%M%S")
    date_str = timestamp.strftime("%Y-%m-%d %H:%M:%S")
    
    # Сохранение итогового результата
    result_filename = f"results/seo_{safe_url}_{timestamp_str}.txt"
    with open(result_filename, "w", encoding="utf-8") as f:
        f.write(f"URL: {url}\n")
        f.write(f"Дата: {date_str}\n")
        f.write("=" * 80 + "\n\n")
        f.write(str(result))
    print(f"\nРезультат сохранён: {result_filename}")
    
    # Сохранение вывода каждой задачи в лог
    log_filename = f"logs/tasks_{safe_url}_{timestamp_str}.log"
    with open(log_filename, "w", encoding="utf-8") as f:
        f.write(f"URL: {url}\n")
        f.write(f"Дата: {date_str}\n")
        f.write("=" * 80 + "\n\n")
        
        for idx, task_output in enumerate(result.tasks_output, 1):
            task_name = task_output.name or task_output.description[:60]
            f.write(f"\n{'='*80}\n")
            f.write(f"ЗАДАЧА {idx}: {task_name}...\n")
            f.write(f"{'='*80}\n")
            f.write(f"Агент: {task_output.agent}\n")
            f.write(f"Описание: {task_output.description}\n")
            if task_output.expected_output:
                f.write(f"Ожидаемый вывод: {task_output.expected_output}\n")
            f.write(f"\n--- ВЫПОЛНЕННЫЙ ВЫВОД ---\n")
            f.write(task_output.raw)
            f.write(f"\n\n")
    
    print(f"Лог задач сохранён: {log_filename}")


def run_seo_analysis(url: str, save_to_file: bool = True):
    """
    Запуск SEO-анализа по URL. Возвращает итоговый отчёт (CrewOutput).
    
    Args:
        url: URL страницы для анализа
        save_to_file: сохранить результат в файл results/ (по умолчанию True)
    
    Returns:
        CrewOutput: результат выполнения Crew
    """
    result = crew.kickoff(inputs={"url": url})
    
    if save_to_file:
        save_result(result, url)
    
    return result


if __name__ == "__main__":
    import sys
    if len(sys.argv) >= 2:
        url = sys.argv[1].strip()
    else:
        url = input("Введите URL страницы для SEO-анализа: ").strip()
        if not url:
            print("URL не указан. Выход.")
            sys.exit(1)
    if not url.startswith(("http://", "https://")):
        url = "https://" + url
    print(f"\nЗапуск SEO-анализа: {url}\n")
    result = run_seo_analysis(url, save_to_file=True)
    print("\n--- Итог ---")
    print(result)
