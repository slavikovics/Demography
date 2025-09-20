import requests
import json


def get_population():
    url = 'https://dataportal.belstat.gov.by/osids-public-api/sdmx-api/indicator/values/SDMX-JSON/10101100004'
    body_scheme = {
        "years": [
            2024,
            2023,
            2022,
            2021,
            2020
        ],
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
        with open('population.json', 'x', encoding='utf-8') as f:
            f.write(resp.text)

    else:
        raise Exception(f'Failed to load population: {resp.status_code}')

    print(f'Response: {resp.text}')


def main():
    get_population()

if __name__ == '__main__':
    main()