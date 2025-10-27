from data_storage.main import main as load_data
from forecasts.population_forecast import build_population_forecasts_for_all_districts
from api.main import main as start_api


def run():
    print('\nStarting api')
    start_api()


if __name__ == '__main__':
    run()