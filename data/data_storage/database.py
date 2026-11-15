import sqlite3
import os
from typing import List, Optional
from models.territory import Territory
from models.population_record import PopulationRecord
from repositories.territory_repository import TerritoryRepository
from repositories.population_repository import PopulationRepository
from repositories.indicator_repository import IndicatorRepository

class DemographyDatabase:
    def __init__(self, db_path: str = "demography.db"):
        self.db_path = db_path
        self.territory_repo = TerritoryRepository(db_path)
        self.population_repo = PopulationRepository(db_path)
        self.indicator_repo = IndicatorRepository(db_path)
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
                model TEXT DEFAULT 'historical',
                UNIQUE(territory_id, gender, year, age_group, type_of_area, model)
            )
        ''')
        
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS indicators (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                territory_id INTEGER NOT NULL,
                indicator_code TEXT NOT NULL,
                year INTEGER NOT NULL,
                value REAL NOT NULL,
                unit TEXT,
                model TEXT NOT NULL DEFAULT 'historical',
                UNIQUE(territory_id, indicator_code, year, model)
            )
        ''')

        cursor.execute('CREATE INDEX IF NOT EXISTS idx_indicators_code_year ON indicators(indicator_code, year)')
        cursor.execute('CREATE INDEX IF NOT EXISTS idx_indicators_territory ON indicators(territory_id)')
        cursor.execute('CREATE INDEX IF NOT EXISTS idx_population_territory ON population(territory_id)')
        cursor.execute('CREATE INDEX IF NOT EXISTS idx_population_year ON population(year)')
        cursor.execute('CREATE INDEX IF NOT EXISTS idx_population_gender ON population(gender)')
        cursor.execute('CREATE INDEX IF NOT EXISTS idx_population_model ON population(model)')
        cursor.execute('CREATE INDEX IF NOT EXISTS idx_territories_parent ON territories(parent_id)')
        
        conn.commit()
        conn.close()

    def get_connection(self):
        return sqlite3.connect(self.db_path)
    
    def insert_territories(self, territories_data):
        return self.territory_repo.insert_territories(territories_data)
    
    def get_territory(self, territory_id: int):
        return self.territory_repo.get_territory(territory_id)
    
    def get_all_territories(self):
        return self.territory_repo.get_all_territories()
    
    def territory_exists(self, territory_id: int) -> bool:
        return self.territory_repo.territory_exists(territory_id)
    
    def delete_territory(self, territory_id: int):
        return self.territory_repo.delete_territory(territory_id)
    
    def insert_population_records(self, population_data):
        return self.population_repo.insert_population_records(population_data)
    
    def get_population_by_territory_and_year(self, territory_id: int, year: int, model: Optional[str] = None):
        return self.population_repo.get_population_by_territory_and_year(territory_id, year, model)
    
    def get_all_available_territory_ids_for_population_forecast(self):
        return self.population_repo.get_all_available_territory_ids()

    def get_available_models(self, territory_id: int):
        """Получить доступные модели прогнозирования для территории"""
        return self.population_repo.get_available_models_for_territory(territory_id)

    def get_population_table(self, year, model, sort_by, sorting_direction):
        return self.population_repo.get_population_table(year, model, sort_by, sorting_direction)

    def get_population_table_fields(self):
        return self.population_repo.get_population_table_fields()

    def get_interesting_data(self, year, model):
        return self.population_repo.get_interesting_data(year, model)
    
    def insert_indicator_records(self, records):
        return self.indicator_repo.insert_indicator_records(records)

    def count_indicator_records(self) -> int:
        return self.indicator_repo.count()

    def get_indicator_by_year(self, indicator_code: str, year: int, model: str = 'historical'):
        return self.indicator_repo.get_by_year(indicator_code, year, model)

    def get_indicator_series(self, indicator_code: str, territory_id: int, model: str = 'historical'):
        return self.indicator_repo.get_series(indicator_code, territory_id, model)

    def get_indicator_years(self, indicator_code: str, model: str = 'historical'):
        return self.indicator_repo.get_available_years(indicator_code, model)

    def get_indicator_table(self, indicator_code: str, year: int, model: str = 'historical',
                            sort_by: str = 'name_ru', sorting_direction: str = 'asc'):
        return self.indicator_repo.get_table(indicator_code, year, model, sort_by, sorting_direction)

    def get_indicator_territory_ids(self, indicator_code: str):
        return self.indicator_repo.get_territory_ids(indicator_code)

    def count_indicator_forecasts(self) -> int:
        return self.indicator_repo.count_forecasts()

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