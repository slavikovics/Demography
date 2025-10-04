import requests
import json
from belstat_parser.dataflow import Dataflow
from belstat_parser.utils import build_years, save_file, load_file, exists


def download_population_datastructures():
    url = "https://dataportal.belstat.gov.by/osids-public-api/sdmx-api/indicator/datastructure/SDMX-JSON/10101200004"
    resp = requests.get(url, timeout=30)
    resp.raise_for_status()
    save_file(resp.text, 'population.json')


def parse_datastructures():
    content = load_file('population.json')
    deserialized = json.loads(content)
    data = deserialized['data']
    dataflow = Dataflow.build_dataflow(data)

    return dataflow


def get_population():
    url = 'https://dataportal.belstat.gov.by/osids-public-api/sdmx-api/indicator/values/SDMX-JSON/10101100004'
    body_scheme = {
        "years": build_years(2020, 2025),
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
            "razrez_594": [
                "699961",
                "919067",
                "919068",
                "919069",
                "919070",
                "919071",
                "919072",
                "919073"
            ],
            "priznak_536": [
                "518105",
                "984726",
                "984727",
                "984728"
            ]
        },
        "simbolsAfterComma": "null"
    }
    resp = requests.post(url=url, json=body_scheme)

    if resp.status_code == 200:
        with open('population.json', 'w', encoding='utf-8') as f:
            f.write(resp.text)

    else:
        raise Exception(f'Failed to load population: {resp.status_code}')

    print(f'Response: {resp.text}')


def main():
    if not exists('population.json'):
        download_population_datastructures()

    dataflow = parse_datastructures()
    print(str(dataflow))


# launch as module
if __name__ == '__main__':
    main()