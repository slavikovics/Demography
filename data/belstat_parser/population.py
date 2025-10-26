import requests
import json
from belstat_parser.dataflow import Dataflow
from belstat_parser.dataset import Dataset
from belstat_parser.file_utils import build_years, save_file, load_file, exists
from belstat_parser.region_utils import extract_district_codes_only


def download_population_datastructures():
    url = "https://dataportal.belstat.gov.by/osids-public-api/sdmx-api/indicator/datastructure/SDMX-JSON/10101100004"
    resp = requests.get(url, timeout=30)
    resp.raise_for_status()
    save_file(resp.text, 'population_scheme.json')


def parse_datastructures():
    content = load_file('population_scheme.json')
    deserialized = json.loads(content)
    data = deserialized['data']
    dataflow = Dataflow.build_dataflow(data)

    return dataflow


def download_population_dataset(dataflow :Dataflow, years = build_years(2010, 2024)):
    url = 'https://dataportal.belstat.gov.by/osids-public-api/sdmx-api/indicator/values/SDMX-JSON/10101100004'
    
    body_scheme = {
        "years": [],
        "periodicities": [],
        "units": [
            "210"
        ],
        "dimensionOrder": [
            "razrez_594",
            "priznak_536",
            "priznak_391",
            "priznak_451"
        ],
        "dimensionParams": {
            "razrez_594": extract_district_codes_only(dataflow),
            "priznak_536": [
                "518105"
            ],
            "priznak_451": [
                "507552"
            ]
        },
        "simbolsAfterComma": "null"
    }

    dataset = None

    for year in years:
        if exists(f'population_data_{year}.json'):
            text = load_file(f'population_data_{year}.json')

            new_dataset = Dataset(json.loads(text), dataflow)
            Dataset.add_year_observation_scheme_to_dataset(new_dataset, year, years)

            if dataset is None:
                dataset = new_dataset
            else:
                dataset.extend(new_dataset)

            continue

        body_scheme["years"] = [year]
        resp = requests.post(url=url, json=body_scheme)

        if resp.status_code == 200:
                save_file(resp.text, f'population_data_{year}.json')

                new_dataset = Dataset(json.loads(resp.text), dataflow)
                Dataset.add_year_observation_scheme_to_dataset(new_dataset, year, years)

                if dataset is None:
                    dataset = new_dataset
                else:
                    dataset.extend(new_dataset)

        else:
            raise Exception(f'Failed to load population: {resp.status_code}. {resp.text}')
    
    return dataset


def get_population(dataflow :Dataflow):
    dataset = download_population_dataset(dataflow)
    save_file(str(dataset), 'population_data')
    return dataset


def get_datastructures():
    if not exists('population_scheme.json'):
        download_population_datastructures()

    return parse_datastructures()


def main():
    dataflow = get_datastructures()
    return get_population(dataflow)


if __name__ == '__main__':
    main()