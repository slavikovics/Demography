class TableRecord:
    def __init__(self, id: int, name_ru: str, name_en: str, people: int):
        self.id = id
        self.name_ru = name_ru
        self.name_en = name_en
        self.people = people
        self.clear_strings()

    def clear_strings(self):
        if self.name_ru:
            self.name_ru = self.name_ru.replace('"', '')
        if self.name_en:
            self.name_en = self.name_en.replace('"', '')

    def to_tuple(self) -> tuple:
        return (
            self.id,
            self.name_ru,
            self.name_en,
            self.people
        )

    def __str__(self) -> str:
        return f"TableRecord(id={self.id}, name_ru='{self.name_ru}', name_en='{self.name_en}', people={self.people})"

    def __repr__(self) -> str:
        return self.__str__()

    @classmethod
    def from_tuple(cls, data: tuple) -> 'TableRecord':
        if len(data) == 4:
            return cls(
                id=data[0],
                name_ru=data[1],
                name_en=data[2],
                people=data[3]
            )
        else:
            raise ValueError(f"Unexpected tuple length: {len(data)}")

    def to_dict(self) -> dict:
        """Конвертация в словарь для API responses"""
        return {
            'id': self.id,
            'name_ru': self.name_ru,
            'name_en': self.name_en,
            'people': self.people
        }