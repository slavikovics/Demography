from belstat_parser.population import get_datastructures
from belstat_parser.population import get_population
from belstat_parser.models import Territory, PopulationRecord


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


def get_populations():
    dataflow = get_datastructures()
    dataset = get_population(dataflow)
    population_records = []

    for observation in dataset.observations:
        population_records.append(PopulationRecord.from_observation(observation))

    return population_records