from typing import Optional


class IndicatorRecord:
    """Одно значение показателя Белстата «как есть» (без пересчётов)."""

    def __init__(self, territory_id: int, indicator_code: str, year: int, value: float,
                 unit: Optional[str] = None, model: str = 'historical', id: Optional[int] = None):
        self.id = id
        self.territory_id = territory_id
        self.indicator_code = indicator_code
        self.year = year
        self.value = value
        self.unit = unit
        self.model = model

    def to_tuple(self) -> tuple:
        return (self.territory_id, self.indicator_code, self.year, self.value, self.unit, self.model)

    def to_dict(self) -> dict:
        return {
            'territory_id': self.territory_id,
            'indicator_code': self.indicator_code,
            'year': self.year,
            'value': self.value,
            'unit': self.unit,
            'model': self.model,
        }

    @classmethod
    def from_row(cls, row: tuple) -> 'IndicatorRecord':
        """row = (territory_id, indicator_code, year, value, unit, model)"""
        return cls(territory_id=row[0], indicator_code=row[1], year=row[2], value=row[3], unit=row[4], model=row[5])

    def __repr__(self) -> str:
        return (f"IndicatorRecord(territory_id={self.territory_id}, indicator_code='{self.indicator_code}', "
                f"year={self.year}, value={self.value}, unit='{self.unit}', model='{self.model}')")
