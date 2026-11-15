import sqlite3

from data_storage.main import main as load_data, load_indicators
from forecasts.population_forecast import build_population_forecasts_for_all_districts
from forecasts.indicator_forecast import build_indicator_forecasts
from api.main import main as start_api

DB_PATH = 'demography.db'


def run():
    print('\nStarting api')
    start_api()


def _count(query):
    try:
        conn = sqlite3.connect(DB_PATH)
        try:
            return conn.execute(query).fetchone()[0]
        finally:
            conn.close()
    except sqlite3.Error:
        return 0


def has_historical_data():
    return _count("SELECT COUNT(*) FROM population WHERE model = 'historical'") > 0


def has_forecasts():
    return _count("SELECT COUNT(*) FROM population WHERE model != 'historical'") > 0


def has_indicators():
    return _count("SELECT COUNT(*) FROM indicators WHERE model = 'historical'") > 0


def has_indicator_forecasts():
    return _count("SELECT COUNT(*) FROM indicators WHERE model != 'historical'") > 0


def prepare_and_run():
    if not has_historical_data():
        print('Loading and parsing data from belstat')
        load_data()
    else:
        print('Historical data already in database, skipping load')

    if not has_indicators():
        print('\nLoading additional indicators from belstat')
        load_indicators()
    else:
        print('Indicators already in database, skipping')

    if not has_forecasts():
        print('\nCreating forecasts (can take significant time)')
        build_population_forecasts_for_all_districts()
    else:
        print('Forecasts already in database, skipping')

    if not has_indicator_forecasts():
        print('\nCreating indicator forecasts')
        build_indicator_forecasts(DB_PATH)
    else:
        print('Indicator forecasts already in database, skipping')

    run()


if __name__ == '__main__':
    prepare_and_run()
