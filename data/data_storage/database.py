import sqlite3
import os
from typing import List, Optional
from models.territory import Territory
from models.population_record import PopulationRecord

class DemographyDatabase:
    def __init__(self, db_path: str = "demography.db"):
        self.db_path = db_path
        self.init_database()
    
    def init_database(self):
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS territories (
                id INTEGER PRIMARY KEY,
                name TEXT NOT NULL,
                name_ru TEXT,
                name_en TEXT,
                parent_id INTEGER
            )
        ''')
        
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS population (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                territory_id INTEGER NOT NULL,
                gender TEXT NOT NULL,
                people INTEGER NOT NULL,
                year INTEGER NOT NULL,
                age_group TEXT,
                type_of_area TEXT,
                UNIQUE(territory_id, gender, year, age_group, type_of_area)
            )
        ''')
        
        cursor.execute('CREATE INDEX IF NOT EXISTS idx_population_territory ON population(territory_id)')
        cursor.execute('CREATE INDEX IF NOT EXISTS idx_population_year ON population(year)')
        cursor.execute('CREATE INDEX IF NOT EXISTS idx_population_gender ON population(gender)')
        cursor.execute('CREATE INDEX IF NOT EXISTS idx_territories_parent ON territories(parent_id)')
        
        conn.commit()
        conn.close()
    
    def insert_territories(self, territories_data):

        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
    
        if not isinstance(territories_data, list):
            territories_data = [territories_data]
    
        inserted_count = 0
    
        for territory in territories_data:
            if isinstance(territory, tuple):
                territory_tuple = territory
            else:
                territory_tuple = territory.to_tuple()
        
            try:
                cursor.execute('''
                    INSERT OR REPLACE INTO territories (id, name, name_ru, name_en, parent_id)
                    VALUES (?, ?, ?, ?, ?)
                ''', territory_tuple)
                inserted_count += 1
            except sqlite3.Error as e:
                print(f"Error inserting territory {territory_tuple}: {e}")
    
        conn.commit()
        conn.close()
    
        return inserted_count
    
    def get_territory(self, territory_id: int):
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute('SELECT * FROM territories WHERE id = ?', (territory_id,))
        result = cursor.fetchone()
        conn.close()
        
        return result
    
    def get_all_territories(self):
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute('SELECT * FROM territories ORDER BY id')
        results = cursor.fetchall()
        conn.close()
        
        return results

    def territory_exists(self, territory_id: int) -> bool:
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute('SELECT 1 FROM territories WHERE id = ?', (territory_id,))
        result = cursor.fetchone() is not None
        conn.close()
        
        return result

    def insert_population_records(self, population_data):
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
    
        if not isinstance(population_data, list):
            population_data = [population_data]
    
        inserted_count = 0
    
        for record in population_data:
            if isinstance(record, tuple):
                record_tuple = record
            else:
                record_tuple = record.to_tuple()
        
            try:
                cursor.execute('''
                    INSERT INTO population (territory_id, gender, people, year, age_group, type_of_area)
                    VALUES (?, ?, ?, ?, ?, ?)
                ''', record_tuple)
                inserted_count += 1
            except sqlite3.Error as e:
                print(f"Error inserting population record {record_tuple}: {e}")
    
        conn.commit()
        conn.close()

        print(f'Inserted {inserted_count} population records')
        return inserted_count
    
    def get_population_by_territory_and_year(self, territory_id: int, year: int):
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute('''
            SELECT gender, people, age_group, type_of_area 
            FROM population 
            WHERE territory_id = ? AND year = ?
        ''', (territory_id, year))
        
        results = cursor.fetchall()
        conn.close()
        return results
    
    def export_to_csv(self, table_name: str, csv_path: str):
        import csv
        
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute(f'SELECT * FROM {table_name}')
        rows = cursor.fetchall()
        
        with open(csv_path, 'w', newline='', encoding='utf-8') as csvfile:
            writer = csv.writer(csvfile)
            writer.writerow([description[0] for description in cursor.description])
            writer.writerows(rows)
        
        conn.close()

    def delete_territory(self, territory_id: int):
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute('DELETE FROM population WHERE territory_id = ?', (territory_id,))
        cursor.execute('DELETE FROM territories WHERE id = ?', (territory_id,))
        
        conn.commit()
        conn.close()