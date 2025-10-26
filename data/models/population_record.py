from typing import Optional


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