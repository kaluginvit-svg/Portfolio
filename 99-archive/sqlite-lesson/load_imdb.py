"""
Скрипт для загрузки данных из CSV файла imdb_top_250.csv в базу данных SQLite.

Использует модуль database.py для работы с базой данных.
"""

import csv
import logging
from database import Database

# Настройка логирования
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    datefmt='%Y-%m-%d %H:%M:%S'
)


def parse_duration(duration_str: str) -> int:
    """
    Преобразует строку длительности (например, "2h 22min") в минуты.
    
    Args:
        duration_str: Строка с длительностью фильма
        
    Returns:
        Длительность в минутах (int) или None
    """
    if not duration_str or duration_str.strip() == '':
        return None
    
    total_minutes = 0
    duration_str = duration_str.strip()
    
    # Обработка часов
    if 'h' in duration_str:
        hours_part = duration_str.split('h')[0].strip()
        try:
            total_minutes += int(hours_part) * 60
        except ValueError:
            pass
        duration_str = duration_str.split('h', 1)[1] if 'h' in duration_str else ''
    
    # Обработка минут
    if 'min' in duration_str:
        minutes_part = duration_str.split('min')[0].strip()
        try:
            total_minutes += int(minutes_part)
        except ValueError:
            pass
    
    return total_minutes if total_minutes > 0 else None


def load_imdb_data(csv_file: str, db_path: str = "imdb_movies.db"):
    """
    Загружает данные из CSV файла в базу данных.
    
    Args:
        csv_file: Путь к CSV файлу
        db_path: Путь к файлу базы данных
    """
    print("=" * 70)
    print("ЗАГРУЗКА ДАННЫХ IMDB TOP 250 В БАЗУ ДАННЫХ")
    print("=" * 70)
    
    # Создание базы данных и таблицы
    print("\n1. Создание базы данных и таблицы...")
    with Database(db_path) as db:
        # Проверяем, существует ли таблица
        if db.table_exists("movies"):
            print("   Таблица 'movies' уже существует. Удаление старой таблицы...")
            db.drop_table("movies", if_exists=True)
        
        # Создание таблицы
        print("   Создание новой таблицы 'movies'...")
        db.create_table("movies", {
            "id": "INTEGER PRIMARY KEY AUTOINCREMENT",
            "rank": "INTEGER NOT NULL",
            "title": "TEXT NOT NULL",
            "year": "INTEGER",
            "genre": "TEXT",
            "duration_minutes": "INTEGER",
            "duration_original": "TEXT",
            "origin": "TEXT",
            "director": "TEXT",
            "imdb_rating": "REAL",
            "rating_count": "INTEGER",
            "imdb_link": "TEXT"
        })
        print("   ✓ Таблица создана успешно")
    
    # Чтение и загрузка данных из CSV
    print("\n2. Чтение данных из CSV файла...")
    movies_data = []
    
    try:
        with open(csv_file, 'r', encoding='utf-8') as file:
            csv_reader = csv.DictReader(file)
            
            for row_num, row in enumerate(csv_reader, start=1):
                # Пропускаем пустые строки
                if not row.get('Title', '').strip():
                    continue
                
                # Извлечение данных из строки
                rank = row.get('', '').strip() or str(row_num)
                try:
                    rank = int(rank) if rank else row_num
                except ValueError:
                    rank = row_num
                
                title = row.get('Title', '').strip()
                year_str = row.get('Year', '').strip()
                genre = row.get('Genre', '').strip()
                duration_original = row.get('Duration', '').strip()
                origin = row.get('Origin', '').strip()
                director = row.get('Director', '').strip()
                rating_str = row.get('IMDB rating', '').strip()
                count_str = row.get('Rating count', '').strip()
                imdb_link = row.get('IMDB link', '').strip()
                
                # Преобразование типов данных
                year = None
                if year_str:
                    try:
                        year = int(year_str)
                    except ValueError:
                        pass
                
                duration_minutes = parse_duration(duration_original)
                
                rating = None
                if rating_str:
                    try:
                        rating = float(rating_str)
                    except ValueError:
                        pass
                
                rating_count = None
                if count_str:
                    try:
                        # Удаляем запятые из числа (например, "2,030,817")
                        count_str = count_str.replace(',', '')
                        rating_count = int(count_str)
                    except ValueError:
                        pass
                
                # Формирование записи для базы данных
                movie_record = {
                    "rank": rank,
                    "title": title,
                    "year": year,
                    "genre": genre if genre else None,
                    "duration_minutes": duration_minutes,
                    "duration_original": duration_original if duration_original else None,
                    "origin": origin if origin else None,
                    "director": director if director else None,
                    "imdb_rating": rating,
                    "rating_count": rating_count,
                    "imdb_link": imdb_link if imdb_link else None
                }
                
                movies_data.append(movie_record)
        
        print(f"   ✓ Прочитано {len(movies_data)} фильмов из CSV файла")
    
    except FileNotFoundError:
        print(f"   ✗ Ошибка: Файл {csv_file} не найден!")
        return
    except Exception as e:
        print(f"   ✗ Ошибка при чтении CSV файла: {e}")
        return
    
    # Загрузка данных в базу данных
    print("\n3. Загрузка данных в базу данных...")
    with Database(db_path) as db:
        try:
            # Используем массовую вставку для эффективности
            db.insert_many("movies", movies_data)
            print(f"   ✓ Успешно загружено {len(movies_data)} фильмов в базу данных")
        except Exception as e:
            print(f"   ✗ Ошибка при загрузке данных: {e}")
            return
    
    # Вывод статистики
    print("\n4. Статистика загруженных данных:")
    print("-" * 70)
    
    with Database(db_path) as db:
        # Общее количество фильмов
        total_count = db.count("movies")
        print(f"   Всего фильмов в базе: {total_count}")
        
        # Самый старый и новый фильм
        oldest = db.fetchone("SELECT title, year FROM movies WHERE year IS NOT NULL ORDER BY year ASC LIMIT 1")
        newest = db.fetchone("SELECT title, year FROM movies WHERE year IS NOT NULL ORDER BY year DESC LIMIT 1")
        
        if oldest:
            print(f"   Самый старый фильм: {oldest['title']} ({oldest['year']} год)")
        if newest:
            print(f"   Самый новый фильм: {newest['title']} ({newest['year']} год)")
        
        # Средний рейтинг
        avg_rating = db.fetchone("SELECT AVG(imdb_rating) as avg_rating FROM movies WHERE imdb_rating IS NOT NULL")
        if avg_rating and avg_rating['avg_rating']:
            print(f"   Средний рейтинг IMDB: {avg_rating['avg_rating']:.2f}")
        
        # Топ-5 фильмов по рейтингу
        top_movies = db.select(
            "movies",
            columns=["rank", "title", "year", "imdb_rating"],
            where="imdb_rating IS NOT NULL",
            order_by="imdb_rating DESC",
            limit=5
        )
        
        if top_movies:
            print("\n   Топ-5 фильмов по рейтингу:")
            for i, movie in enumerate(top_movies, 1):
                print(f"   {i}. {movie['title']} ({movie['year']}) - {movie['imdb_rating']}")
        
        # Статистика по жанрам
        genre_stats = db.fetchall(
            """
            SELECT genre, COUNT(*) as count 
            FROM movies 
            WHERE genre IS NOT NULL AND genre != ''
            GROUP BY genre 
            ORDER BY count DESC 
            LIMIT 5
            """
        )
        
        if genre_stats:
            print("\n   Топ-5 жанров:")
            for stat in genre_stats:
                print(f"   - {stat['genre']}: {stat['count']} фильмов")
        
        # Статистика по странам
        origin_stats = db.fetchall(
            """
            SELECT origin, COUNT(*) as count 
            FROM movies 
            WHERE origin IS NOT NULL AND origin != ''
            GROUP BY origin 
            ORDER BY count DESC 
            LIMIT 5
            """
        )
        
        if origin_stats:
            print("\n   Топ-5 стран производства:")
            for stat in origin_stats:
                print(f"   - {stat['origin']}: {stat['count']} фильмов")
    
    print("\n" + "=" * 70)
    print("ЗАГРУЗКА ЗАВЕРШЕНА УСПЕШНО!")
    print("=" * 70)
    print(f"\nБаза данных создана: {db_path}")
    print(f"Таблица: movies")
    print(f"Загружено записей: {len(movies_data)}")


if __name__ == "__main__":
    # Путь к CSV файлу
    csv_file = "imdb_top_250.csv"
    
    # Путь к базе данных
    db_path = "base.db"
    
    # Загрузка данных
    load_imdb_data(csv_file, db_path)
