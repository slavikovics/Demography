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

class PopulationRecord:
    def __init__(self, territory_id: int, gender: str, people: int, year: int, 
                 age_group: Optional[str] = None, type_of_area: Optional[str] = None, 
                 id: Optional[int] = None):
        self.id = id
        self.territory_id = territory_id
        self.gender = gender
        self.people = people
        self.year = year
        self.age_group = age_group
        self.type_of_area = type_of_area
        self.clear_strings()

    def clear_strings(self):
        self.gender = self.gender.replace('"', '')
        self.age_group = self.age_group.replace('"', '')
        self.type_of_area = self.type_of_area.replace('"', '')
    
    def to_tuple(self) -> tuple:
        return (
            self.territory_id,
            self.gender,
            self.people,
            self.year,
            self.age_group,
            self.type_of_area
        )
    
    def to_tuple_with_id(self) -> tuple:
        return (
            self.id,
            self.territory_id,
            self.gender,
            self.people,
            self.year,
            self.age_group,
            self.type_of_area
        )
    
    def __str__(self) -> str:
        id_info = f"id={self.id}, " if self.id is not None else ""
        age_info = f", age_group='{self.age_group}'" if self.age_group else ""
        area_info = f", type_of_area='{self.type_of_area}'" if self.type_of_area else ""
        return f"PopulationRecord({id_info}territory_id={self.territory_id}, gender='{self.gender}', people={self.people}, year={self.year}{age_info}{area_info})"
    
    def __repr__(self) -> str:
        return self.__str__()
    
    @classmethod
    def from_tuple(cls, data: tuple) -> 'PopulationRecord':
        return cls(
            id=data[0],
            territory_id=data[1],
            gender=data[2],
            people=data[3],
            year=data[4],
            age_group=data[5],
            type_of_area=data[6]
        )
    
    @classmethod
    def from_observation(cls, observation) -> 'PopulationRecord':
        territory_id = None
        age_group = None
        gender = None
        type_of_area = None
        year = None
        
        for i, (mask_value, mask_obj) in enumerate(observation.mask_list):
            if i == 0:  # Territory
                territory_id = int(observation.observation_schemes[i].get_real_id_by_mask_id(mask_value))
            elif i == 1:  # Age group
                age_group = str(mask_obj) if mask_obj else None
            elif i == 2:  # Gender
                gender = str(mask_obj) if mask_obj else None
            elif i == 3:  # Type of area
                type_of_area = str(mask_obj) if mask_obj else None
            elif i == 5:  # Year
                year = int(mask_obj.name)
        
        try:
            people = int(float(observation.value))
        except (ValueError, TypeError):
            people = 0
        
        return cls(
            territory_id=territory_id,
            gender=gender or "Unknown",
            people=people,
            year=year,
            age_group=age_group,
            type_of_area=type_of_area
        )