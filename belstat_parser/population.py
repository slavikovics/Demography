import requests
import zipfile
import json
import os
from belstat_parser.dataflow import Dataflow

DATASTRUCTURES_PATH = 'datastructures.json'

def build_years(start_year :int, end_year :int):
    return [year for year in range(start_year, end_year + 1)]


def save_datastructures():
    url = "https://dataportal.belstat.gov.by/osids-public-api/sdmx-api/indicator/datastructure/SDMX-JSON/10101100004"
    resp = requests.get(url, timeout=30)
    resp.raise_for_status()

    with open(DATASTRUCTURES_PATH, 'w', encoding='utf-8') as f:
        f.write(resp.text)


def parse_datastructures():
    with open(DATASTRUCTURES_PATH, 'r', encoding='utf-8') as file:
        content = file.read()

    deserialized = json.loads(content)
    data = deserialized['data']
    dataflow = Dataflow.build_dataflow(data)

    return dataflow


def json_from_bytes(resp):
    with open("1063261_rubric_indicators_values.zip", "wb") as f:
        for chunk in resp.iter_content(chunk_size=8192):
            f.write(chunk)

    with zipfile.ZipFile("1063261_rubric_indicators_values.zip") as zf:
        zf.extractall("1063261_data")
    return


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
    if not os.path.exists(DATASTRUCTURES_PATH):
        save_datastructures()

    dataflow = parse_datastructures()
    print(str(dataflow))


if __name__ == '__main__':
    main()