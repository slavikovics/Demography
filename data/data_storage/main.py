from belstat_parser.parser import get_populations, get_territories
from belstat_parser.indicators import get_indicator_records
from data_storage.database import DemographyDatabase


def main():
    database = DemographyDatabase()
    territories = get_territories()
    populations = get_populations()

    database.insert_territories(territories)
    database.insert_population_records(populations)


def load_indicators(db_path: str = "demography.db"):
    """Загрузка дополнительных показателей (рождаемость, смертность, миграция,
    браки/разводы, плотность). Население и прогнозы не затрагивает."""
    database = DemographyDatabase(db_path)
    records = get_indicator_records()
    database.insert_indicator_records(records)


if __name__ == '__main__':
    main()
