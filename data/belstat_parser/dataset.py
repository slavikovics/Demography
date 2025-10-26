from belstat_parser.observation import ObservationScheme, Observation
from belstat_parser.dataflow import Dataflow
from belstat_parser.value import ObservationValue


class Dataset:

    def __init__(self, data, dataflow :Dataflow):
        self.dataflow = dataflow
        self.datasets = data['dataSets']
        self.structure = data['structure']
        self.observation_schemes = []
        self.observation_schemes_structure = self.structure['dimensions']['observation']
        self.load_observation_schemes()
        self.observations = []
        self.load_observations()

    def load_observation_schemes(self):
        for observation_structure in self.observation_schemes_structure:
            self.observation_schemes.append(ObservationScheme(data=observation_structure, dataflow=self.dataflow))

    def load_observations(self):
        dataset = self.datasets[0]
        for mask, data in dataset['observations'].items():
            self.observations.append(Observation(self.parse_numbers_before_dash(mask), data, self.observation_schemes))

    def parse_numbers_before_dash(self, input_string):
        numbers = []
        for part in input_string.split(':'):
            if '-' in part:
                break
            try:
                numbers.append(int(part))
            except ValueError:
                continue
        return numbers
    
    def extract_key_value_pairs(self, data_dict):
        results = []
    
        for key, value_list in data_dict:
            key_numbers = self.parse_numbers_before_dash(key)
            results.append((key_numbers, value_list))
    
        return results
    
    def __str__(self):
        result = ''
        for i, observation in enumerate(self.observations):
            result += f'{i + 1}. ' + str(observation) + '\n\n'

        return result
    
    def extend(self, other):
        for observation in other.observations:
            self.observations.append(observation)

    def add_observation_scheme(self, observation_scheme: ObservationScheme, observation_mask_value):
        self.observation_schemes.append(observation_scheme)

        for observation in self.observations:
            observation.mask.append(observation_mask_value)
            observation.observation_schemes.append(observation_scheme)
            observation.mask_list = []
            observation.resolve_mask_list()

    @staticmethod
    def add_year_observation_scheme_to_dataset(dataset, selected_year, years):
        values = []
        selected_value = None

        for i, year in enumerate(years):
            value = ObservationValue(index=i, name=year)
            values.append(value)

            if year == selected_year:
                selected_value = i

        scheme = ObservationScheme(name='year', values=values)
        dataset.add_observation_scheme(scheme, selected_value)
    