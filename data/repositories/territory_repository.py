import sqlite3
from typing import List, Optional
from models.territory import Territory

class TerritoryRepository:
    def __init__(self, db_path: str):
        self.db_path = db_path
    
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

    def delete_territory(self, territory_id: int):
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute('DELETE FROM population WHERE territory_id = ?', (territory_id,))
        cursor.execute('DELETE FROM territories WHERE id = ?', (territory_id,))
        
        conn.commit()
        conn.close()