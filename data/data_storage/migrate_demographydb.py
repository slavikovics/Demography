# migration_add_model_column.py
import sqlite3

def migrate_database():
    conn = sqlite3.connect('demography.db')
    cursor = conn.cursor()
    
    # Добавляем столбец model если его нет
    try:
        cursor.execute('ALTER TABLE population ADD COLUMN model TEXT DEFAULT "historical"')
        print("Added model column to population table")
    except sqlite3.OperationalError as e:
        if "duplicate column name" in str(e):
            print("Model column already exists")
        else:
            raise e
    
    # Обновляем существующие записи
    cursor.execute('UPDATE population SET model = "historical" WHERE model IS NULL')
    print("Updated existing records with historical model")
    
    conn.commit()
    conn.close()
    print("Migration completed successfully")

if __name__ == "__main__":
    migrate_database()