from belstat_parser.concept import Concept


class ObservationValue:

    def __init__(self, index, data=None, concept: Concept=None, name=None):
        self.index = index
        if data is not None and concept is not None:
            self.code_id = data['id']
            self.name = data['name']
            self.code = concept.get_code_by_id(self.code_id)
        elif name is not None:
            self.code_id = index
            self.name = name
            self.code = None
        else:
            raise ValueError("Invalid arguments for ObservationValue initialization")

    def __str__(self):
        return f'"{self.name}"'