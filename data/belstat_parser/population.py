import requests
import json
from belstat_parser.dataflow import Dataflow
from belstat_parser.dataset import Dataset
from belstat_parser.utils import build_years, save_file, load_file, exists
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


def download_population(dataflow :Dataflow):
    url = 'https://dataportal.belstat.gov.by/osids-public-api/sdmx-api/indicator/values/SDMX-JSON/10101100004'
    year = 2015
    body_scheme = {
        "years": [year],
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
    resp = requests.post(url=url, json=body_scheme)

    if resp.status_code == 200:
        save_file(resp.text, 'population_data.json')

    else:
        raise Exception(f'Failed to load population: {resp.status_code}. {resp.text}')


def get_population(dataflow :Dataflow):
    if not exists('population_data.json'):
        download_population(dataflow)

    content = load_file('population_data.json')
    dataset = Dataset(json.loads(content), dataflow)
    print(str(dataset))


def main():
    if not exists('population_scheme.json'):
        download_population_datastructures()

    dataflow = parse_datastructures()
    print(dataflow)
    get_population(dataflow)


# launch as module
if __name__ == '__main__':
    main()