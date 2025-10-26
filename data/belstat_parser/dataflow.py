from typing import Optional
from belstat_parser.concept import Concept

class Dataflow:

    def __init__(self, dataflow_name_en, dataflow_name_ru, concepts):
        self.dataflow_name_en = dataflow_name_en
        self.dataflow_name_ru = dataflow_name_ru
        self.concepts = concepts

    def __str__(self):
        header = f'Dataflow \"{self.dataflow_name_en}\":\n'
        content = '\n'.join([str(concept) for concept in self.concepts])
        return header + content

    @staticmethod
    def build_dataflow(data):
        try:
            dataflow_name_en = data['dataflows'][0]['names']['en']
            dataflow_name_ru = data['dataflows'][0]['names']['ru']
            concept_schemes = data['conceptSchemes'][0]['concepts']
            concepts = Concept.build_all_concepts_for_dataflow(concept_schemes, data['codelists'])

            return Dataflow(dataflow_name_en, dataflow_name_ru, concepts)

        except:
            raise Exception('Failed to parse Dataflow.')

    def get_concept_by_id(self, concept_id) -> Optional[Concept]:
        for concept in self.concepts:
            if concept.concept_id == concept_id:
                return concept

        return None