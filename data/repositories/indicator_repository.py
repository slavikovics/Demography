import sqlite3
from typing import List


class IndicatorRepository:
    def __init__(self, db_path: str):
        self.db_path = db_path

    def _connect(self):
        return sqlite3.connect(self.db_path, timeout=30)

    def insert_indicator_records(self, records) -> int:
        """Вставка/обновление значений (идемпотентно по territory_id + indicator_code + year + model)."""
        if not isinstance(records, list):
            records = [records]

        rows = [r if isinstance(r, tuple) else r.to_tuple() for r in records]

        conn = self._connect()
        try:
            conn.executemany('''
                INSERT OR REPLACE INTO indicators (territory_id, indicator_code, year, value, unit, model)
                VALUES (?, ?, ?, ?, ?, ?)
            ''', rows)
            conn.commit()
        finally:
            conn.close()

        print(f'Inserted {len(rows)} indicator records')
        return len(rows)

    def _scalar(self, query: str, params=()):
        conn = self._connect()
        try:
            return conn.execute(query, params).fetchone()[0]
        finally:
            conn.close()

    def count(self) -> int:
        """Число исторических значений."""
        return self._scalar("SELECT COUNT(*) FROM indicators WHERE model = 'historical'")

    def count_forecasts(self) -> int:
        return self._scalar("SELECT COUNT(*) FROM indicators WHERE model != 'historical'")

    def _fetch(self, query: str, params) -> List[tuple]:
        conn = self._connect()
        try:
            return conn.execute(query, params).fetchall()
        finally:
            conn.close()

    def get_by_year(self, indicator_code: str, year: int, model: str = 'historical') -> List[tuple]:
        """Значения показателя по всем территориям за год."""
        return self._fetch('''
            SELECT territory_id, indicator_code, year, value, unit, model
            FROM indicators
            WHERE indicator_code = ? AND year = ? AND model = ?
            ORDER BY territory_id
        ''', (indicator_code, year, model))

    def get_series(self, indicator_code: str, territory_id: int, model: str = 'historical') -> List[tuple]:
        """Временной ряд показателя для территории."""
        return self._fetch('''
            SELECT territory_id, indicator_code, year, value, unit, model
            FROM indicators
            WHERE indicator_code = ? AND territory_id = ? AND model = ?
            ORDER BY year
        ''', (indicator_code, territory_id, model))

    def get_available_years(self, indicator_code: str, model: str = 'historical') -> List[int]:
        rows = self._fetch(
            'SELECT DISTINCT year FROM indicators WHERE indicator_code = ? AND model = ? ORDER BY year',
            (indicator_code, model))
        return [row[0] for row in rows]

    def get_territory_ids(self, indicator_code: str) -> List[int]:
        rows = self._fetch(
            "SELECT DISTINCT territory_id FROM indicators WHERE indicator_code = ? AND model = 'historical'",
            (indicator_code,))
        return [row[0] for row in rows]

    def get_table(self, indicator_code: str, year: int, model: str = 'historical',
                  sort_by: str = 'name_ru', sorting_direction: str = 'asc') -> List[tuple]:
        """Строки для таблицы: (id, name_ru, name_en, value, unit)."""
        allowed_columns = {'id': 'i.territory_id', 'name_ru': 't.name_ru',
                           'name_en': 't.name_en', 'value': 'i.value'}
        if sort_by not in allowed_columns:
            raise ValueError(f"Invalid sort column: {sort_by}")
        if (sorting_direction or 'asc').upper() not in ('ASC', 'DESC'):
            raise ValueError(f"Invalid sort direction: {sorting_direction}")

        return self._fetch(f'''
            SELECT i.territory_id, t.name_ru, t.name_en, i.value, i.unit
            FROM indicators i
            JOIN territories t ON t.id = i.territory_id
            WHERE i.indicator_code = ? AND i.year = ? AND i.model = ?
            ORDER BY {allowed_columns[sort_by]} {sorting_direction.upper()}
        ''', (indicator_code, year, model))

