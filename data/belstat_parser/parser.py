from belstat_parser.population import get_datastructures
from belstat_parser.population import get_population
from models.territory import Territory
from models.population_record import PopulationRecord


def get_territories():
    dataflow = get_datastructures()
    territory_concept = None

    for concept in dataflow.concepts:
        if concept.concept_id == 'razrez_594':
            territory_concept = concept
            break

    territory_codes = territory_concept.codes
    territories = []

    for territory_code in territory_codes:
        territories.append(Territory.from_code(territory_code))

    return territories


def find_record(records, territory_id, other):
    for record in records:
        if record.territory_id == territory_id and record.year == other.year and record.gender == other.gender and record.age_group == other.age_group and record.type_of_area == other.type_of_area:
            return record
    
    return None


def find_all_records_with_territory_id(records, territory_id):
    result = []

    for record in records:
        if record.territory_id == territory_id:
            result.append(record)
    
    return result


def insert_regional_city_to_district(population_records, city_id, district_id):
    district_records_for_all_time = find_all_records_with_territory_id(population_records, district_id)

    for record in district_records_for_all_time:

        city_record = find_record(population_records, city_id, record)
        district_record = record

        if city_record is None or district_record is None:
            print(f'Failed to find regional city or district')

        start_amount = district_record.people
        district_record.people += city_record.people

        print(f'District had {start_amount} people. City had {city_record.people}. Now district has {district_record.people}.')


def process_regional_cities(population_records):
    insert_regional_city_to_district(population_records, 919093, 919075)
    insert_regional_city_to_district(population_records, 919092, 919077)
    insert_regional_city_to_district(population_records, 919094, 919088)
    insert_regional_city_to_district(population_records, 919118, 919099)
    insert_regional_city_to_district(population_records, 919119, 919108)
    insert_regional_city_to_district(population_records, 919145, 919126)
    insert_regional_city_to_district(population_records, 919165, 919150)
    insert_regional_city_to_district(population_records, 919200, 919193)
    insert_regional_city_to_district(population_records, 919225, 919203)
    insert_regional_city_to_district(population_records, 919224, 919215)


def get_populations():
    dataflow = get_datastructures()
    dataset = get_population(dataflow)
    population_records = []

    for observation in dataset.observations:
        population_records.append(PopulationRecord.from_observation(observation))

    process_regional_cities(population_records)

    return population_records