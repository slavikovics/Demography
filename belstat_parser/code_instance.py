class Code:

    def __init__(self, code_id, urn, name, name_ru, name_en, parent_id):
        self.code_id = code_id
        self.urn = urn
        self.name = name
        self.name_ru = name_ru
        self.name_en = name_en
        self.parent_id = parent_id
        self.parent = None

    def __str__(self):
        if self.parent is None:
            return f'Code \"{self.name_en}\", id: \"{self.code_id}\".'

        return f'Code \"{self.name_en}\", id: \"{self.code_id}\". --> Parent: \"{str(self.parent)}\"'

    def resolve_parent(self, codes):
        if self.parent_id is None:
            return

        for code in codes:
            if code.code_id == self.parent_id:
                self.parent = code
                return

        raise Exception(f'Failed to resolve parent for code: {self.name_en}, id: {self.code_id}')

    @staticmethod
    def build_code(code):
        try:
            code_id = code['id']
            urn = code['urn']
            name = code['name']

            try:
                name_ru = code['names']['ru']
            except KeyError:
                name_ru = 'N/A'

            try:
                name_en = code['names']['en']
            except KeyError:
                name_en = 'N/A'

            parent_id = code['parent']

            if parent_id is not None and str(parent_id) == '':
                parent_id = None

            return Code(code_id, urn, name, name_ru, name_en, parent_id)

        except:
            raise Exception('Failed to parse code.')

    @staticmethod
    def transform_concept_id(concept_id):
        return 'CL_' + concept_id

    @staticmethod
    def build_all_codes_for_concept(code_lists, concept_id):
        codes = []

        for code_list in code_lists:
            if code_list['id'] !=  Code.transform_concept_id(concept_id):
                continue

            for code in code_list['codes']:
                codes.append(Code.build_code(code))

            for code in codes:
                code.resolve_parent(codes)

            return codes

        #raise Exception(f'Failed to find code_list for concept_id: {concept_id}')