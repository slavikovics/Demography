from belstat_parser.parser import get_populations, get_territories
from data_storage.database import DemographyDatabase


def main():
    database = DemographyDatabase()
    territories = get_territories()
    populations = get_populations()

    database.insert_territories(territories)
    database.insert_population_records(populations)


if __name__ == '__main__':
    main()