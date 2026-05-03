from database import Database

def delete_movies_older_than_2005_and_vacuum():
    delete_query = "DELETE FROM movies WHERE year < ?;"
    delete_params = (2005,)

    with Database("base.db") as db:
        db.execute(delete_query, delete_params)
        db.commit()

def main():
    confirm = input(
        "Точно удалить фильмы старше 2005 года и выполнить VACUUM? (yes/no): "
    ).strip().lower()

    if confirm == "yes":
        delete_movies_older_than_2005_and_vacuum()
        print("Удаление и VACUUM выполнены.")
    else:
        print("Операция отменена.")

if __name__ == "__main__":
    main()



