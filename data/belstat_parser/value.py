from belstat_parser.concept import Concept


class ObservationValue:

    def __init__(self, start_i, data, concept :Concept):
        self.start_i = start_i
        self.code_id = data['id']
        self.name = data['name']
        self.code = concept.get_code_by_id(self.code_id)

    def __str__(self):
        return f'"{self.name}"'