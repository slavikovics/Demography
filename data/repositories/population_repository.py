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
                       WHERE territory_id = ?
                         AND model IS NOT NULL
                       ''', (territory_id,))

        results = [row[0] for row in cursor.fetchall()]
        conn.close()
        return results

    def get_population_table_fields(self):
        return ['id', 'name_ru', 'name_en', 'people']

    def get_population_table(self, year, model, sort_by, sorting_direction):
        # Валидация параметров для защиты от SQL-инъекций
        allowed_columns = ['id', 'name_ru', 'name_en', 'people']
        allowed_directions = ['ASC', 'DESC']

        if sort_by not in allowed_columns:
            raise ValueError(f"Invalid sort column: {sort_by}")
        if sorting_direction.upper() not in allowed_directions:
            raise ValueError(f"Invalid sort direction: {sort_by}")

        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

        query = f'''
            SELECT population.id AS id, name_ru, name_en, people
            FROM population
            JOIN territories ON population.territory_id = territories.id
            WHERE year = {year} AND gender = 'Total'
            AND model = '{model}'
            ORDER BY {sort_by} {sorting_direction}
        '''

        try:
            cursor.execute(query)
            results = cursor.fetchall()
            conn.close()
        except sqlite3.Error as e:
            print(f"Database error: {e}")
            conn.close()
            raise

        return results

    def get_interesting_data(self, year, model):
        results = []
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        query = f'''
            SELECT name_ru, name_en, people
            FROM population
            JOIN territories ON population.territory_id = territories.id
            WHERE year = {year} AND gender = 'Total' AND model = '{model}'
            ORDER BY people ASC
            LIMIT 1
        '''
        cursor.execute(query)
        results.append(cursor.fetchall())
        query = f'''
            SELECT name_ru, name_en, people
            FROM (
                SELECT 
                    t.name_ru, 
                    t.name_en, 
                    p.people,
                    RANK() OVER (ORDER BY p.people DESC) as rank
                FROM population p
                JOIN territories t ON p.territory_id = t.id
                WHERE year = {year} AND gender = 'Total' AND model = '{model}'
            ) ranked
            WHERE rank = 2;
        '''
        cursor.execute(query)
        results.append(cursor.fetchall())

        prev_year = year - 1
        prev_year_model = model
        if prev_year <= 2024:
            prev_year_model = 'historical'

        query = f'''
            SELECT name_ru, name_en, people_growth
            FROM (
                SELECT 
                    t.name_ru, 
                    t.name_en, 
                    (p24.people - p23.people) as people_growth,
                    ROW_NUMBER() OVER (ORDER BY (p24.people - p23.people) ASC) as row_num
                FROM territories t
                    JOIN population p24 ON t.id = p24.territory_id
                    JOIN population p23 ON t.id = p23.territory_id
                WHERE p24.year = {year} 
                        AND p23.year = {prev_year}
                        AND p24.gender = 'Total'
                        AND p23.gender = 'Total'
                        AND p23.model = '{prev_year_model}'
                        AND p24.model = '{model}'
            ) ranked
            WHERE row_num = 2;
        '''
        cursor.execute(query)
        results.append(cursor.fetchall())
        query = f'''
            SELECT 
                t.name_ru, 
                t.name_en, 
                (p24.people - p23.people) as people_growth
            FROM territories t
                JOIN population p24 ON t.id = p24.territory_id
                JOIN population p23 ON t.id = p23.territory_id
            WHERE p24.year = {year} 
                    AND p23.year = {prev_year}
                    AND p24.gender = 'Total'
                    AND p23.gender = 'Total'
                    AND p23.model = '{prev_year_model}'
                    AND p24.model = '{model}'
            ORDER BY people_growth DESC
            LIMIT 1;
        '''
        cursor.execute(query)
        results.append(cursor.fetchall())

        conn.close()

        return results

