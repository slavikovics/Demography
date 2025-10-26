from typing import Optional


class Territory:
    def __init__(self, id: int, name: str, name_ru: Optional[str] = None, name_en: Optional[str] = None, parent_id: Optional[int] = None):
        self.id = id
        self.name = name
        self.name_ru = name_ru
        self.name_en = name_en
        self.parent_id = parent_id
        self.clear_strings()
    
    def to_tuple(self) -> tuple:
        return (self.id, self.name, self.name_ru, self.name_en, self.parent_id)
    
    def clear_strings(self):
        self.name = self.name.replace('"', '')
        self.name_ru = self.name_ru.replace('"', '')
        self.name_en = self.name_en.replace('"', '')
    
    def __str__(self) -> str:
        parent_info = f", parent_id={self.parent_id}" if self.parent_id is not None else ""
        ru_info = f", name_ru='{self.name_ru}'" if self.name_ru else ""
        en_info = f", name_en='{self.name_en}'" if self.name_en else ""
        return f"Territory(id={self.id}, name='{self.name}'{ru_info}{en_info}{parent_info})"
    
    def __repr__(self) -> str:
        return self.__str__()
    
    @classmethod
    def from_tuple(cls, data: tuple) -> 'Territory':
        return cls(
            id=data[0],
            name=data[1],
            name_ru=data[2],
            name_en=data[3],
            parent_id=data[4]
        )
    
    @classmethod
    def from_code(cls, territory_code) -> 'Territory':
        return cls(
            id=territory_code.code_id,
            name=territory_code.name,
            name_ru=territory_code.name_ru,
            name_en=territory_code.name_en,
            parent_id=territory_code.parent_id
        )