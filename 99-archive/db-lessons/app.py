#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
SQL Игра - Веб-версия
Flask приложение для обучения SQL через браузер
"""

from flask import Flask, render_template, request, jsonify, session
import sqlite3
import os
import re
from typing import Tuple, List, Optional

app = Flask(__name__)
app.secret_key = 'sql_game_secret_key_2024'  # Для сессий

DB_PATH = 'products_orders.db'
GAME_DB = 'sql_game.db'

def init_game_db():
    """Инициализация базы данных игры"""
    if not os.path.exists(GAME_DB):
        conn = sqlite3.connect(GAME_DB)
        cursor = conn.cursor()
        
        # Создание схемы
        with open('sql_game_schema.sql', 'r', encoding='utf-8') as f:
            cursor.executescript(f.read())
        
        # Заполнение заданий
        with open('sql_game_tasks.sql', 'r', encoding='utf-8') as f:
            cursor.executescript(f.read())
        
        conn.commit()
        conn.close()

def get_columns_from_query(query: str) -> List[str]:
    """Извлечение столбцов из запроса"""
    try:
        conn = sqlite3.connect(DB_PATH)
        cursor = conn.cursor()
        cursor.execute(query)
        columns = [description[0] for description in cursor.description]
        conn.close()
        return columns
    except:
        return []

def check_query(user_query: str, task: dict) -> Tuple[bool, str, Optional[List], Optional[List]]:
    """
    Проверка SQL запроса
    Возвращает: (правильность, сообщение, результат, столбцы)
    """
    try:
        conn = sqlite3.connect(DB_PATH)
        cursor = conn.cursor()
        cursor.execute(user_query)
        result = cursor.fetchall()
        columns = [desc[0] for desc in cursor.description]
        conn.close()
        
        # Проверка столбцов
        expected_cols = [col.strip() for col in task['expected_columns'].split(',')]
        user_cols = [col.lower() for col in columns]
        expected_cols_lower = [col.lower() for col in expected_cols]
        
        cols_match = True
        if len(user_cols) != len(expected_cols_lower):
            cols_match = False
        else:
            for i, expected in enumerate(expected_cols_lower):
                if expected not in user_cols[i] and user_cols[i] not in expected:
                    if not any(func in user_cols[i] for func in ['count', 'avg', 'sum', 'min', 'max']):
                        cols_match = False
                        break
        
        if not cols_match:
            return False, f"Неверные столбцы. Ожидалось: {task['expected_columns']}, получено: {', '.join(columns)}", None, None
        
        # Проверка количества строк
        if task.get('expected_row_count'):
            if len(result) != task['expected_row_count']:
                return False, f"Неверное количество строк. Ожидалось: {task['expected_row_count']}, получено: {len(result)}", None, None
        
        # Проверка категории
        query_upper = user_query.upper()
        category = task['category']
        
        category_checks = {
            'SELECT': 'SELECT' in query_upper,
            'WHERE': 'WHERE' in query_upper,
            'LIKE': 'LIKE' in query_upper,
            'ORDER_BY': 'ORDER BY' in query_upper,
            'GROUP_BY': 'GROUP BY' in query_upper,
            'HAVING': 'HAVING' in query_upper,
            'JOIN': 'JOIN' in query_upper,
            'JOIN_GROUP': 'JOIN' in query_upper and 'GROUP BY' in query_upper,
            'AGGREGATE': any(func in query_upper for func in ['COUNT', 'AVG', 'SUM', 'MIN', 'MAX'])
        }
        
        if category in category_checks and not category_checks[category]:
            return False, f"Запрос должен использовать {category.replace('_', ' ')}", None, None
        
        return True, "✓ Запрос правильный!", result[:20], columns
        
    except sqlite3.Error as e:
        return False, f"Ошибка SQL: {str(e)}", None, None
    except Exception as e:
        return False, f"Ошибка: {str(e)}", None, None

@app.route('/')
def index():
    """Главная страница"""
    return render_template('index.html')

@app.route('/game')
def game():
    """Страница игры"""
    level = request.args.get('level', 1, type=int)
    return render_template('game.html', level=level)

@app.route('/api/tasks')
def get_tasks():
    """API: Получение заданий по уровню"""
    level = request.args.get('level', 1, type=int)
    
    conn = sqlite3.connect(GAME_DB)
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()
    cursor.execute('''
        SELECT id, level, title, description, hint, sql_example, 
               expected_columns, expected_row_count, points, category
        FROM tasks
        WHERE level = ?
        ORDER BY id
    ''', (level,))
    
    tasks = [dict(row) for row in cursor.fetchall()]
    conn.close()
    
    return jsonify(tasks)

@app.route('/api/check', methods=['POST'])
def check_answer():
    """API: Проверка ответа"""
    data = request.json
    task_id = data.get('task_id')
    query = data.get('query', '').strip()
    player_name = session.get('player_name', 'Игрок')
    
    if not query:
        return jsonify({'success': False, 'message': 'Пустой запрос!'})
    
    # Получаем задание
    conn = sqlite3.connect(GAME_DB)
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()
    cursor.execute('SELECT * FROM tasks WHERE id = ?', (task_id,))
    task_row = cursor.fetchone()
    
    if not task_row:
        conn.close()
        return jsonify({'success': False, 'message': 'Задание не найдено'})
    
    task = dict(task_row)
    conn.close()
    
    # Проверяем запрос
    is_correct, message, result, columns = check_query(query, task)
    
    # Сохраняем результат
    points = task['points'] if is_correct else 0
    conn = sqlite3.connect(GAME_DB)
    cursor = conn.cursor()
    cursor.execute('''
        INSERT INTO player_results (player_name, task_id, sql_query, is_correct, points_earned)
        VALUES (?, ?, ?, ?, ?)
    ''', (player_name, task_id, query, is_correct, points))
    conn.commit()
    conn.close()
    
    return jsonify({
        'success': is_correct,
        'message': message,
        'result': result[:10] if result else None,
        'columns': columns if columns else None,
        'points': points
    })

@app.route('/api/stats')
def get_stats():
    """API: Получение статистики игрока"""
    player_name = session.get('player_name', 'Игрок')
    
    conn = sqlite3.connect(GAME_DB)
    cursor = conn.cursor()
    cursor.execute('''
        SELECT 
            COUNT(*) as total_attempts,
            SUM(CASE WHEN is_correct THEN 1 ELSE 0 END) as correct_attempts,
            SUM(points_earned) as total_points
        FROM player_results
        WHERE player_name = ?
    ''', (player_name,))
    
    row = cursor.fetchone()
    conn.close()
    
    return jsonify({
        'total_attempts': row[0] or 0,
        'correct_attempts': row[1] or 0,
        'total_points': row[2] or 0
    })

@app.route('/api/set_player', methods=['POST'])
def set_player():
    """API: Установка имени игрока"""
    data = request.json
    player_name = data.get('name', 'Игрок').strip()
    session['player_name'] = player_name
    return jsonify({'success': True, 'name': player_name})

if __name__ == '__main__':
    # Инициализация БД игры
    init_game_db()
    
    # Проверка основной БД
    if not os.path.exists(DB_PATH):
        print(f"⚠ Внимание: База данных {DB_PATH} не найдена!")
        print("Сначала создайте базу данных products_orders.db")
    
    print("\n" + "="*60)
    print("SQL ИГРА - ВЕБ-ВЕРСИЯ")
    print("="*60)
    print("\nОткройте в браузере: http://localhost:5000")
    print("Для остановки нажмите Ctrl+C\n")
    
    app.run(debug=True, host='127.0.0.1', port=5000)
