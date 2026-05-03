import sqlite3
import os
import sys

def find_db_files():
    files = [f for f in os.listdir('.') if f.endswith('.db')]
    return files

def prompt_selection(options, prompt_text):
    if not options:
        return None
    print(prompt_text)
    for i, opt in enumerate(options, 1):
        print(f"{i}. {opt}")
    
    while True:
        try:
            choice = input("Введите номер (или нажмите Enter для выбора первого): ").strip()
            if not choice:
                return options[0]
            idx = int(choice) - 1
            if 0 <= idx < len(options):
                return options[idx]
            print("Неверный номер.")
        except ValueError:
            print("Пожалуйста, введите число.")

def sanitize_filename(value):
    name = []
    for ch in value:
        if ch.isalnum() or ch in ("_", "-", ".", " "):
            name.append(ch)
        else:
            name.append("_")
    cleaned = "".join(name).strip().strip(".")
    return cleaned or "search_results"

def export_to_new_db(source_rows, column_names, search_term):
    safe_tag = sanitize_filename(search_term)
    new_db_name = f"search_results_{safe_tag}.db"
    
    if os.path.exists(new_db_name):
        print(f"Файл {new_db_name} уже существует. Перезаписываем...")
        try:
            os.remove(new_db_name)
        except OSError as e:
            print(f"Ошибка при удалении старого файла: {e}")
            return

    try:
        new_conn = sqlite3.connect(new_db_name)
        new_cursor = new_conn.cursor()
        
        # Construct CREATE TABLE statement dynamically based on columns
        cols_def = ", ".join([f'"{col}" TEXT' for col in column_names]) # Using TEXT for simplicity for all imported cols or try to preserve types?
        # Actually better to just assume structure or use generic typing. SQLite is flexible.
        # But we want to preserve Primary Key if possible? Not strictly necessary for export view.
        
        create_sql = f"CREATE TABLE posts ({cols_def})"
        new_cursor.execute(create_sql)
        
        placeholders = ", ".join(["?"] * len(column_names))
        insert_sql = f"INSERT INTO posts VALUES ({placeholders})"
        
        new_cursor.executemany(insert_sql, source_rows)
        new_conn.commit()
        new_conn.close()
        
        print(f"\n✅ Результаты успешно сохранены в базе: {new_db_name}")
        print(f"Всего сохранено записей: {len(source_rows)}")
        
    except sqlite3.Error as e:
        print(f"Ошибка при создании базы экспорта: {e}")

def search_posts(db_path, search_term):
    print(f"\nПоиск в {db_path} по запросу '{search_term}'...\n")
    try:
        conn = sqlite3.connect(db_path)
        # Use row_factory to access columns by name if needed, but here we just need raw values
        cursor = conn.cursor()
        
        # Select ALL columns to pass to new DB
        query = "SELECT * FROM posts WHERE text_flat LIKE ?"
        cursor.execute(query, (f"%{search_term}%",))
        
        rows = cursor.fetchall()
        
        if not rows:
            print("Ничего не найдено.")
            return

        # Get column names from valid query
        column_names = [description[0] for description in cursor.description]

        print(f"Найдено совпадений: {len(rows)}")
        print("-" * 40)
        
        # Look for specific columns for display
        try:
            idx_channel = column_names.index("channel_name")
            idx_id = column_names.index("message_id")
            idx_text = column_names.index("text_flat")
        except ValueError:
            # Fallback if columns differ
            idx_channel = 0
            idx_id = 1
            idx_text = -1 # assumes last or present

        for i, row in enumerate(rows):
            if i >= 5: # Limit preview to 5 items
                print(f"... и еще {len(rows) - 5} сообщений")
                break
                
            channel_name = row[idx_channel]
            msg_id = row[idx_id]
            text = row[idx_text] if idx_text != -1 else str(row)
            
            display_text = text[:200].replace('\n', ' ') + "..." if len(text) > 200 else text.replace('\n', ' ')
            
            print(f"[{channel_name}] ID: {msg_id}")
            print(f"Сообщение: {display_text}")
            print("-" * 40)
        
        export_to_new_db(rows, column_names, search_term)

                
    except sqlite3.Error as e:
        print(f"Ошибка базы данных: {e}")
    finally:
        if conn:
            conn.close()

def main():
    db_files = find_db_files()
    if not db_files:
        print("В текущей директории не найдены файлы .db.")
        return

    if len(db_files) == 1:
        db_path = db_files[0]
        print(f"Используется база данных: {db_path}")
    else:
        db_path = prompt_selection(db_files, "Выберите базу данных:")
    
    if not db_path:
        return

    search_term = input("Введите тег или ключевое слово для поиска: ").strip()
    if not search_term:
        print("Пустой запрос. Выход.")
        return

    search_posts(db_path, search_term)

if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\nSearch cancelled.")
