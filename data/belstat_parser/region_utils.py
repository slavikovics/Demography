from belstat_parser.code import Code
from belstat_parser.dataflow import Dataflow


def extract_district_codes_only(dataflow :Dataflow):
    territory = dataflow.get_concept_by_id('razrez_594')
    codes = territory.get_all_codes()
    districts = []

    for code in codes:
        if code.parent is not None and 'region' in code.parent.name_en.lower() or code.code_id == '919071':
            districts.append(code.code_id)

    return districts






