from belstat_parser.observation import ObservationScheme, Observation
from belstat_parser.dataflow import Dataflow


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
            self.observation_schemes.append(ObservationScheme(observation_structure, self.dataflow))

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

    
    