import sqlite3
from typing import List, Optional
from models.population_record import PopulationRecord

class PopulationRepository:
    def __init__(self, db_path: str):
        self.db_path = db_path
    
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
                    INSERT INTO population (territory_id, gender, people, year, age_group, type_of_area, model)
                    VALUES (?, ?, ?, ?, ?, ?, ?)
                ''', record_tuple)
                inserted_count += 1
            except sqlite3.Error as e:
                print(f"Error inserting population record {record_tuple}: {e}")
    
        conn.commit()
        conn.close()

        print(f'Inserted {inserted_count} population records')
        return inserted_count
    
    def get_population_by_territory_and_year(self, territory_id: int, year: int, model: Optional[str] = None):
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        if model:
            cursor.execute('''
                SELECT id, territory_id, gender, people, year, age_group, type_of_area, model
                FROM population 
                WHERE territory_id = ? AND year = ? AND model = ?
            ''', (territory_id, year, model))
        else:
            cursor.execute('''
                SELECT id, territory_id, gender, people, year, age_group, type_of_area, model
                FROM population 
                WHERE territory_id = ? AND year = ?
            ''', (territory_id, year))
        
        results = cursor.fetchall()
        conn.close()
        return results
    
    def get_all_available_territory_ids(self):
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        cursor.execute('''
            SELECT DISTINCT territory_id 
            FROM population
        ''')
        
        results = [row[0] for row in cursor.fetchall()]
        conn.close()
        return results

    def get_available_models_for_territory(self, territory_id: int):
        """Получить доступные модели прогнозирования для территории"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        cursor.execute('''
            SELECT DISTINCT model 
            FROM population 
            WHERE territory_id = ? AND model IS NOT NULL
        ''', (territory_id,))
        
        results = [row[0] for row in cursor.fetchall()]
        conn.close()
        return results