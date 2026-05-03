#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
SQL Игра - Обучалка по SQL запросам
Игра дает задания разной сложности, пользователь вводит SQL запрос,
система проверяет правильность.
"""

import sqlite3
import os
import re
from typing import Tuple, List, Optional

class SQLGame:
    def __init__(self, db_path: str = 'products_orders.db', game_db: str = 'sql_game.db'):
        self.db_path = db_path  # База с данными (products, orders)
        self.game_db = game_db  # База с заданиями
        self.player_name = ""
        self.current_level = 1
        self.total_points = 0
        
    def setup_game_db(self):
        """Создание базы данных игры с заданиями"""
        conn = sqlite3.connect(self.game_db)
        cursor = conn.cursor()
        
        # Читаем и выполняем схему
        with open('sql_game_schema.sql', 'r', encoding='utf-8') as f:
            schema = f.read()
            cursor.executescript(schema)
        
        # Читаем и выполняем задания
        with open('sql_game_tasks.sql', 'r', encoding='utf-8') as f:
            tasks = f.read()
            cursor.executescript(tasks)
        
        conn.commit()
        conn.close()
        print("✓ База данных игры создана!")
    
    def normalize_sql(self, sql: str) -> str:
        """Нормализация SQL запроса для сравнения"""
        # Убираем лишние пробелы, приводим к верхнему регистру
        sql = re.sub(r'\s+', ' ', sql.strip())
        sql = sql.upper()
        # Убираем точку с запятой в конце
        if sql.endswith(';'):
            sql = sql[:-1]
        return sql.strip()
    
    def get_columns_from_query(self, query: str) -> List[str]:
        """Извлечение списка столбцов из SELECT запроса"""
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            cursor.execute(query)
            columns = [description[0] for description in cursor.description]
            conn.close()
            return columns
        except:
            return []
    
    def check_query(self, user_query: str, task: dict) -> Tuple[bool, str, Optional[List]]:
        """
        Проверка SQL запроса пользователя
        Возвращает: (правильность, сообщение, результат запроса)
        """
        try:
            # Выполняем запрос пользователя
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            cursor.execute(user_query)
            result = cursor.fetchall()
            columns = [desc[0] for desc in cursor.description]
            conn.close()
            
            # Проверяем столбцы
            expected_cols = [col.strip() for col in task['expected_columns'].split(',')]
            user_cols = [col.lower() for col in columns]
            expected_cols_lower = [col.lower() for col in expected_cols]
            
            # Проверка столбцов (с учетом возможных псевдонимов)
            cols_match = True
            if len(user_cols) != len(expected_cols_lower):
                cols_match = False
            else:
                for i, expected in enumerate(expected_cols_lower):
                    # Разрешаем псевдонимы и функции
                    if expected not in user_cols[i] and user_cols[i] not in expected:
                        # Проверяем функции (COUNT, AVG, SUM и т.д.)
                        if not any(func in user_cols[i] for func in ['count', 'avg', 'sum', 'min', 'max']):
                            cols_match = False
                            break
            
            if not cols_match:
                return False, f"Неверные столбцы. Ожидалось: {task['expected_columns']}, получено: {', '.join(columns)}", None
            
            # Проверка количества строк (если указано)
            if task.get('expected_row_count'):
                if len(result) != task['expected_row_count']:
                    return False, f"Неверное количество строк. Ожидалось: {task['expected_row_count']}, получено: {len(result)}", None
            
            # Проверка структуры запроса (базовая)
            query_upper = user_query.upper()
            
            # Проверка категории задания
            category = task['category']
            if category == 'SELECT' and 'SELECT' not in query_upper:
                return False, "Запрос должен содержать SELECT", None
            elif category == 'WHERE' and 'WHERE' not in query_upper:
                return False, "Запрос должен содержать WHERE", None
            elif category == 'LIKE' and 'LIKE' not in query_upper:
                return False, "Запрос должен использовать LIKE", None
            elif category == 'ORDER_BY' and 'ORDER BY' not in query_upper:
                return False, "Запрос должен содержать ORDER BY", None
            elif category == 'GROUP_BY' and 'GROUP BY' not in query_upper:
                return False, "Запрос должен содержать GROUP BY", None
            elif category == 'HAVING' and 'HAVING' not in query_upper:
                return False, "Запрос должен содержать HAVING", None
            elif 'JOIN' in category and 'JOIN' not in query_upper:
                return False, "Запрос должен использовать JOIN", None
            
            return True, "✓ Запрос правильный!", result[:10]  # Возвращаем первые 10 строк
            
        except sqlite3.Error as e:
            return False, f"Ошибка SQL: {str(e)}", None
        except Exception as e:
            return False, f"Ошибка: {str(e)}", None
    
    def get_tasks_by_level(self, level: int) -> List[dict]:
        """Получение заданий по уровню"""
        conn = sqlite3.connect(self.game_db)
        cursor = conn.cursor()
        cursor.execute('''
            SELECT id, level, title, description, hint, sql_example, 
                   expected_columns, expected_row_count, points, category
            FROM tasks
            WHERE level = ?
            ORDER BY id
        ''', (level,))
        
        tasks = []
        for row in cursor.fetchall():
            tasks.append({
                'id': row[0],
                'level': row[1],
                'title': row[2],
                'description': row[3],
                'hint': row[4],
                'sql_example': row[5],
                'expected_columns': row[6],
                'expected_row_count': row[7],
                'points': row[8],
                'category': row[9]
            })
        
        conn.close()
        return tasks
    
    def save_result(self, task_id: int, query: str, is_correct: bool, points: int):
        """Сохранение результата выполнения задания"""
        conn = sqlite3.connect(self.game_db)
        cursor = conn.cursor()
        cursor.execute('''
            INSERT INTO player_results (player_name, task_id, sql_query, is_correct, points_earned)
            VALUES (?, ?, ?, ?, ?)
        ''', (self.player_name, task_id, query, is_correct, points))
        conn.commit()
        conn.close()
    
    def get_statistics(self) -> dict:
        """Получение статистики игрока"""
        conn = sqlite3.connect(self.game_db)
        cursor = conn.cursor()
        
        cursor.execute('''
            SELECT 
                COUNT(*) as total_attempts,
                SUM(CASE WHEN is_correct THEN 1 ELSE 0 END) as correct_attempts,
                SUM(points_earned) as total_points
            FROM player_results
            WHERE player_name = ?
        ''', (self.player_name,))
        
        row = cursor.fetchone()
        conn.close()
        
        return {
            'total_attempts': row[0] or 0,
            'correct_attempts': row[1] or 0,
            'total_points': row[2] or 0
        }
    
    def play_level(self, level: int):
        """Игра на определенном уровне"""
        tasks = self.get_tasks_by_level(level)
        
        if not tasks:
            print(f"Нет заданий для уровня {level}")
            return
        
        print(f"\n{'='*60}")
        print(f"УРОВЕНЬ {level}")
        print(f"{'='*60}\n")
        
        for i, task in enumerate(tasks, 1):
            print(f"\nЗадание {i}/{len(tasks)}: {task['title']}")
            print(f"Описание: {task['description']}")
            print(f"Категория: {task['category']}")
            print(f"Очки: {task['points']}")
            
            attempts = 0
            max_attempts = 3
            
            while attempts < max_attempts:
                attempts += 1
                print(f"\nПопытка {attempts}/{max_attempts}")
                user_query = input("Введите SQL запрос: ").strip()
                
                if not user_query:
                    print("Пустой запрос!")
                    continue
                
                # Проверка запроса
                is_correct, message, result = self.check_query(user_query, task)
                print(f"\n{message}")
                
                if is_correct:
                    points = task['points']
                    if attempts > 1:
                        points = int(points * 0.8)  # Штраф за повторные попытки
                    
                    self.total_points += points
                    self.save_result(task['id'], user_query, True, points)
                    
                    print(f"✓ Выполнено! Заработано очков: {points}")
                    if result:
                        print(f"\nРезультат (первые строки):")
                        for row in result[:5]:
                            print(f"  {row}")
                    break
                else:
                    self.save_result(task['id'], user_query, False, 0)
                    
                    if attempts < max_attempts:
                        show_hint = input("\nПоказать подсказку? (y/n): ").strip().lower()
                        if show_hint == 'y':
                            print(f"\nПодсказка: {task['hint']}")
                    else:
                        print(f"\nПравильный ответ: {task['sql_example']}")
            
            print(f"\n{'─'*60}")
    
    def start_game(self):
        """Запуск игры"""
        print("="*60)
        print("SQL ИГРА - ОБУЧАЛКА ПО SQL")
        print("="*60)
        
        # Проверка базы данных игры
        if not os.path.exists(self.game_db):
            print("\nСоздание базы данных игры...")
            self.setup_game_db()
        
        # Имя игрока
        self.player_name = input("\nВведите ваше имя: ").strip()
        if not self.player_name:
            self.player_name = "Игрок"
        
        # Проверка основной базы данных
        if not os.path.exists(self.db_path):
            print(f"\n⚠ Ошибка: База данных {self.db_path} не найдена!")
            print("Сначала создайте базу данных products_orders.db")
            return
        
        # Главное меню
        while True:
            print("\n" + "="*60)
            print("ГЛАВНОЕ МЕНЮ")
            print("="*60)
            print("1. Играть (уровень 1)")
            print("2. Играть (уровень 2)")
            print("3. Играть (уровень 3)")
            print("4. Играть (уровень 4)")
            print("5. Играть (уровень 5)")
            print("6. Статистика")
            print("7. Выход")
            
            choice = input("\nВыберите действие: ").strip()
            
            if choice == '7':
                print(f"\nСпасибо за игру, {self.player_name}!")
                print(f"Итого очков: {self.total_points}")
                break
            elif choice == '6':
                stats = self.get_statistics()
                print(f"\nСтатистика игрока {self.player_name}:")
                print(f"Всего попыток: {stats['total_attempts']}")
                print(f"Правильных: {stats['correct_attempts']}")
                print(f"Всего очков: {stats['total_points']}")
            elif choice in ['1', '2', '3', '4', '5']:
                level = int(choice)
                self.play_level(level)
            else:
                print("Неверный выбор!")

if __name__ == "__main__":
    game = SQLGame()
    game.start_game()
