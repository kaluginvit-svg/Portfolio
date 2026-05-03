"""
Система управления проектами и задачами
Демонстрация работы системы
"""

import sys
import io
from datetime import date

# Исправление кодировки для Windows
if sys.platform == 'win32':
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')
    sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding='utf-8')

from models import User, TaskStatus, ProjectRole
from services import ProjectService, TaskService


def main():
    """Демонстрационный пример использования системы управления задачами"""
    
    print("=" * 70)
    print("СИСТЕМА УПРАВЛЕНИЯ ПРОЕКТАМИ И ЗАДАЧАМИ")
    print("=" * 70)
    
    # Инициализация сервисов
    project_service = ProjectService()
    task_service = TaskService()
    
    # ========== 1. Создание пользователей ==========
    print("\n" + "─" * 70)
    print("1. СОЗДАНИЕ ПОЛЬЗОВАТЕЛЕЙ")
    print("─" * 70)
    
    alice = User(username="Alice", email="alice@example.com")
    bob = User(username="Bob", email="bob@example.com")
    charlie = User(username="Charlie", email="charlie@example.com")
    
    print(f"\nСоздан пользователь: {alice}")
    print(f"Создан пользователь: {bob}")
    print(f"Создан пользователь: {charlie}")
    
    # ========== 2. Создание проекта ==========
    print("\n" + "─" * 70)
    print("2. СОЗДАНИЕ ПРОЕКТА")
    print("─" * 70)
    
    web_project = project_service.create_project(
        user=alice,
        name="Веб-приложение",
        description="Разработка корпоративного веб-приложения"
    )
    
    # ========== 3. Добавление участников в проект ==========
    print("\n" + "─" * 70)
    print("3. ДОБАВЛЕНИЕ УЧАСТНИКОВ В ПРОЕКТ")
    print("─" * 70)
    
    # Alice (администратор) добавляет Bob как участника
    project_service.add_user_to_project(
        acting_user=alice,
        project=web_project,
        target_user=bob,
        role=ProjectRole.MEMBER
    )
    
    # Alice добавляет Charlie как гостя
    project_service.add_user_to_project(
        acting_user=alice,
        project=web_project,
        target_user=charlie,
        role=ProjectRole.GUEST
    )
    
    # Попытка Bob (не администратора) добавить пользователя (должна быть отклонена)
    david = User(username="David", email="david@example.com")
    project_service.add_user_to_project(
        acting_user=bob,
        project=web_project,
        target_user=david,
        role=ProjectRole.MEMBER
    )
    
    # ========== 4. Создание задач ==========
    print("\n" + "─" * 70)
    print("4. СОЗДАНИЕ ЗАДАЧ")
    print("─" * 70)
    
    task1 = task_service.create_task(
        user=alice,
        project=web_project,
        project_service=project_service,
        title="Разработать дизайн главной страницы",
        description="Создать макет в Figma",
        due_date=date(2026, 2, 1)
    )
    
    task2 = task_service.create_task(
        user=bob,
        project=web_project,
        project_service=project_service,
        title="Настроить базу данных",
        description="Установить PostgreSQL и создать схему"
    )
    
    task3 = task_service.create_task(
        user=alice,
        project=web_project,
        project_service=project_service,
        title="Написать документацию API"
    )
    
    # Попытка создать задачу пользователем вне проекта
    eve = User(username="Eve", email="eve@example.com")
    task_service.create_task(
        user=eve,
        project=web_project,
        project_service=project_service,
        title="Взломать систему"
    )
    
    # ========== 5. Назначение ответственных за задачи ==========
    print("\n" + "─" * 70)
    print("5. НАЗНАЧЕНИЕ ОТВЕТСТВЕННЫХ ЗА ЗАДАЧИ")
    print("─" * 70)
    
    if task1:
        task_service.assign_task(
            acting_user=alice,
            task=task1,
            target_user=bob,
            project_service=project_service
        )
    
    if task2:
        task_service.assign_task(
            acting_user=bob,
            task=task2,
            target_user=bob,
            project_service=project_service
        )
    
    if task3:
        task_service.assign_task(
            acting_user=alice,
            task=task3,
            target_user=charlie,
            project_service=project_service
        )
    
    # ========== 6. Работа с задачами ==========
    print("\n" + "─" * 70)
    print("6. РАБОТА С ЗАДАЧАМИ")
    print("─" * 70)
    
    if task1:
        print("\n--- Установка срока выполнения ---")
        task1.set_due_date(date(2026, 1, 25))
    
    if task2:
        print("\n--- Изменение статуса задачи ---")
        task_service.change_task_status(
            user=bob,
            task=task2,
            new_status=TaskStatus.IN_PROGRESS,
            project_service=project_service
        )
        
        print("\n--- Завершение задачи ---")
        task2.mark_as_done()
    
    if task1:
        print("\n--- Повторное открытие задачи ---")
        task1.reopen()
    
    # ========== 7. Получение списка задач проекта ==========
    print("\n" + "─" * 70)
    print("7. ПОЛУЧЕНИЕ СПИСКА ЗАДАЧ ПРОЕКТА")
    print("─" * 70)
    
    tasks = project_service.get_project_tasks(
        user=alice,
        project=web_project,
        task_service=task_service
    )
    
    print("\nЗадачи в проекте:")
    for i, task in enumerate(tasks, 1):
        assignee_info = ""
        if task.assignee_id:
            # Находим имя ответственного
            for u in [alice, bob, charlie]:
                if u.id == task.assignee_id:
                    assignee_info = f" | Ответственный: {u.username}"
                    break
        
        due_info = f" | Срок: {task.due_date}" if task.due_date else ""
        print(f"  {i}. '{task.title}' [{task.status.value}]{assignee_info}{due_info}")
    
    # Попытка получить задачи пользователем вне проекта
    project_service.get_project_tasks(
        user=eve,
        project=web_project,
        task_service=task_service
    )
    
    # ========== 8. Работа с профилем пользователя ==========
    print("\n" + "─" * 70)
    print("8. ОБНОВЛЕНИЕ ПРОФИЛЯ ПОЛЬЗОВАТЕЛЯ")
    print("─" * 70)
    
    print()
    alice.update_profile("Alice_Admin")
    
    # ========== 9. Управление проектом ==========
    print("\n" + "─" * 70)
    print("9. УПРАВЛЕНИЕ ПРОЕКТОМ")
    print("─" * 70)
    
    print("\n--- Изменение названия проекта ---")
    web_project.change_name("Корпоративный веб-портал")
    
    print("\n--- Создание второго проекта ---")
    mobile_project = project_service.create_project(
        user=bob,
        name="Мобильное приложение",
        description="iOS и Android приложение"
    )
    
    print("\n--- Архивация проекта ---")
    mobile_project.archive()
    
    print("\n--- Попытка изменить заархивированный проект ---")
    mobile_project.change_name("Новое название")
    
    # ========== 10. Итоговая статистика ==========
    print("\n" + "═" * 70)
    print("ИТОГОВАЯ СТАТИСТИКА СИСТЕМЫ")
    print("═" * 70)
    
    print(f"\nВсего пользователей: {len([alice, bob, charlie, eve, david])}")
    print(f"Всего проектов: {len(project_service.projects)}")
    print(f"Активных проектов: {len([p for p in project_service.projects if not p.is_archived])}")
    print(f"Заархивированных проектов: {len([p for p in project_service.projects if p.is_archived])}")
    print(f"Всего задач: {len(task_service.tasks)}")
    print(f"Выполненных задач: {len([t for t in task_service.tasks if t.status == TaskStatus.DONE])}")
    print(f"В работе: {len([t for t in task_service.tasks if t.status == TaskStatus.IN_PROGRESS])}")
    print(f"Всего участников в проектах: {len(project_service.memberships)}")
    
    print("\n" + "═" * 70)
    print("ДЕМОНСТРАЦИЯ ЗАВЕРШЕНА")
    print("═" * 70)


if __name__ == "__main__":
    main()
