import os
import json

with open('config.json', 'r', encoding='utf-8') as config:
    data = config.read()

DATASTRUCTURES_PATH = json.loads(data)['data_structures_path']
os.makedirs(DATASTRUCTURES_PATH, exist_ok=True)


def build_years(start_year :int, end_year :int):
    return [year for year in range(start_year, end_year + 1)]


def save_file(text, sub_path):
    with open(os.path.join(DATASTRUCTURES_PATH, sub_path), 'w', encoding='utf-8') as f:
        f.write(text)


def load_file(sub_path):
    with open(os.path.join(DATASTRUCTURES_PATH, sub_path), 'r', encoding='utf-8') as file:
        content = file.read()

    return content


def exists(sub_path):
    if not os.path.exists(os.path.join(DATASTRUCTURES_PATH, sub_path)):
        return False

    return True