from typing import List, Tuple
from belstat_parser.dataflow import Dataflow
from belstat_parser.value import ObservationValue


class ObservationScheme:
    def __init__(self, data, dataflow :Dataflow):
        self.concept_id = data['id']
        self.concept = dataflow.get_concept_by_id(self.concept_id)
        self.name = data['name']
        self.key_position = data['keyPosition']
        self.values_structure = data['values']
        self.values = []
        self.load_values()

    def load_values(self):
        start_i = 0
        for value in self.values_structure:
            self.values.append(ObservationValue(start_i, value, self.concept))
            start_i += 1

    def get_value_by_id(self, value_id):
        for value in self.values:
            if value_id == value.start_i:
                return value
        return None


class Observation:

    def __init__(self, observation_mask, data, obsrvation_schemes):
        self.mask = observation_mask
        self.value = data[0]
        self.observation_schemes = obsrvation_schemes
        self.mask_list = []
        self.resolve_mask_dict()

    def resolve_mask_dict(self):
        for i, number in enumerate(self.mask):
            self.mask_list.append((i, self.observation_schemes[i].get_value_by_id(number)))

    def __str__(self):
        result = 'Observation \nMask: '
        for key, value in self.mask_list:
            result += f'{key}: {value} '

        result += f'\nValue: {self.value}'
        return result