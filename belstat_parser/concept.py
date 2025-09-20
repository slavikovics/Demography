from belstat_parser.code_instance import Code

class Concept:

    def __init__(self, concept_id, concept_urn, concept_name, concept_name_en, concept_name_ru):
        self.concept_id = concept_id
        self.concept_urn = concept_urn
        self.concept_name = concept_name
        self.concept_name_en = concept_name_en
        self.concept_name_ru = concept_name_ru
        self.codes = None

    def __str__(self):
        header = f'\nConcept \"{self.concept_name_en}\", id: \"{self.concept_id}\".'
        if self.codes is None:
            return header

        content = '\n---CODES---\n' + '\n'.join([str(code) for code in self.codes])
        return header + content

    @staticmethod
    def build_concept(concept, code_lists):
        try:
            concept_id = concept['id']
            concept_urn = concept['urn']
            concept_name = concept['name']

            try:
                concept_name_ru = concept['names']['ru']
            except KeyError:
                concept_name_ru = 'N/A'

            try:
                concept_name_en = concept['names']['en']
            except KeyError:
                concept_name_en = 'N/A'

            result = Concept(concept_id, concept_urn, concept_name, concept_name_en, concept_name_ru)
            result.codes = Code.build_all_codes_for_concept(code_lists, concept_id)
            return result

        except:
            raise Exception('Failed to find some values to create Concept.')

    @staticmethod
    def build_all_concepts_for_dataflow(concepts, code_lists):
        result = []

        try:
            for concept in concepts:
                result.append(Concept.build_concept(concept, code_lists))

        except Exception as e:
            raise Exception(f'Failed to parse concepts.')

        return result