"""Загрузка дополнительных демографических показателей Белстата (как есть).

Для каждого показателя берётся срез «всего» по всем дополнительным измерениям
(пол, тип местности, возраст, причина смерти, поток миграции и т.д.).
Территории те же, что и у населения: районы, города областного подчинения,
г. Минск и республика в целом (см. region_utils.extract_district_codes_only).
"""
import json
import re
from concurrent.futures import ThreadPoolExecutor
from typing import Dict, List, Optional

import requests

from belstat_parser.file_utils import build_years, exists, load_file, save_file
from belstat_parser.parser import get_datastructures, get_raw_populations
from belstat_parser.region_utils import extract_district_codes_only
from indicator_catalog import ADDITIVE_CODES, DENSITY_CODE, INDICATORS, RATE_CODES, REGIONAL_CITY_PAIRS  # noqa: F401
from models.indicator_record import IndicatorRecord

API = 'https://dataportal.belstat.gov.by/osids-public-api/sdmx-api/indicator'

DEFAULT_YEARS = build_years(2010, 2025)


_TOTAL = re.compile(r'^(Оба пола|Всего|По всем|всего)', re.I)


def _name(code: dict) -> str:
    names = code.get('names') or {}
    return names.get('ru') or names.get('en') or code.get('name') or ''


def _pick_total(codes: List[dict]) -> str:
    for code in codes:
        if _TOTAL.search(_name(code)):
            return code['id']
    for code in codes:
        if not code.get('parent'):
            return code['id']
    return codes[0]['id']


def _codelist_id(dimension: dict) -> str:
    # urn:...Codelist=BELSTAT:CL_xxx(1.0)  ->  CL_xxx
    return dimension['localRepresentation']['enumeration'].split('=')[-1].split('(')[0].split(':')[-1]


def _structure(code: str) -> dict:
    cache = f'indicator_{code}_structure.json'
    if exists(cache):
        return json.loads(load_file(cache))
    resp = requests.get(f'{API}/datastructure/SDMX-JSON/{code}', timeout=30)
    resp.raise_for_status()
    save_file(resp.text, cache)
    return json.loads(resp.text)


def build_request_body(code: str, year: int, territory_ids: List[str]) -> tuple:
    """Возвращает (тело запроса, название единицы измерения)."""
    data = _structure(code)['data']
    codelists = {c['id']: c for c in data['codelists']}
    dimensions = data['dataStructures'][0]['dataStructureComponents']['dimensionList']['dimensions']

    order, params = [], {}
    unit_id, unit_name = None, None

    for dimension in dimensions:
        dim_id = dimension['id']
        codelist = codelists[_codelist_id(dimension)]

        if dim_id.startswith('unit_'):
            unit_id, unit_name = codelist['codes'][0]['id'], _name(codelist['codes'][0])
            continue

        order.append(dim_id)
        if dim_id == 'razrez_594':
            params[dim_id] = territory_ids
        else:
            params[dim_id] = [_pick_total(codelist['codes'])]

    body = {
        'years': [year],
        'periodicities': [],
        'units': [unit_id],
        'dimensionOrder': order,
        'dimensionParams': params,
        'simbolsAfterComma': 'null',
    }
    return body, unit_name


def parse_values(text: str, code: str, year: int, unit: Optional[str]) -> List[IndicatorRecord]:
    data = json.loads(text)
    observations = data['dataSets'][0].get('observations') or {}
    dimensions = data['structure']['dimensions']['observation']
    territory_dim = next(i for i, d in enumerate(dimensions) if d['id'] == 'razrez_594')

    records = []
    for mask, values in observations.items():
        if not values or values[0] in (None, ''):
            continue
        index = int(mask.split(':')[territory_dim])
        territory_id = int(dimensions[territory_dim]['values'][index]['id'])
        try:
            value = float(values[0])
        except (TypeError, ValueError):
            continue
        records.append(IndicatorRecord(territory_id, code, year, value, unit))
    return records


def fetch_indicator_year(code: str, year: int, territory_ids: List[str]) -> List[IndicatorRecord]:
    cache = f'indicator_{code}_{year}.json'
    unit = None
    body, unit = build_request_body(code, year, territory_ids)

    if exists(cache):
        text = load_file(cache)
    else:
        resp = requests.post(f'{API}/values/SDMX-JSON/{code}', json=body, timeout=120)
        if resp.status_code != 200:
            raise Exception(f'Failed to load indicator {code} for {year}: {resp.status_code}. {resp.text[:200]}')
        text = resp.text
        records = parse_values(text, code, year, unit)
        # пустые ответы (например, 2020–2023 для естественного движения) не кэшируем:
        # Белстат может опубликовать их позже
        if records:
            save_file(text, cache)
        return records

    return parse_values(text, code, year, unit)


def build_population_weights() -> Dict[tuple, int]:
    """Население (оба пола) по (territory_id, year) без слияния городов с районами."""
    weights = {}
    for record in get_raw_populations():
        if record.gender == 'Total' and record.people:
            weights[(record.territory_id, record.year)] = record.people
    return weights


def _population(weights: Dict[tuple, int], territory_id: int, year: int) -> Optional[int]:
    """Население территории за год; если года нет (например, 2025), берётся ближайший предыдущий."""
    for y in range(year, 2000, -1):
        if (territory_id, y) in weights:
            return weights[(territory_id, y)]
    return None


def merge_regional_cities(records: List[IndicatorRecord], weights: Dict[tuple, int]) -> Dict[str, int]:
    """Аналог process_regional_cities для населения: показатели города областного
    подчинения добавляются к району (записи самих городов остаются как есть).

    - абсолютные значения складываются;
    - коэффициенты на 1000 усредняются с весом по населению;
    - плотность пересчитывается через площадь (площадь = население / плотность).
    """
    index = {(r.territory_id, r.indicator_code, r.year): r for r in records}
    stats = {'merged': 0, 'skipped': 0}

    for city_id, district_id in REGIONAL_CITY_PAIRS:
        for (territory_id, code, year), district in list(index.items()):
            if territory_id != district_id:
                continue
            city = index.get((city_id, code, year))
            if city is None:
                stats['skipped'] += 1
                continue

            if code in ADDITIVE_CODES:
                district.value += city.value
            else:
                pop_d = _population(weights, district_id, year)
                pop_c = _population(weights, city_id, year)
                if not pop_d or not pop_c:
                    stats['skipped'] += 1
                    continue

                if code in RATE_CODES:
                    district.value = round((district.value * pop_d + city.value * pop_c) / (pop_d + pop_c), 1)
                elif code == DENSITY_CODE:
                    if district.value <= 0 or city.value <= 0:
                        stats['skipped'] += 1
                        continue
                    area = pop_d / district.value + pop_c / city.value
                    district.value = round((pop_d + pop_c) / area, 1)
            stats['merged'] += 1

    return stats


def get_indicator_records(indicator_codes=None, years=None, workers: int = 4) -> List[IndicatorRecord]:
    indicator_codes = indicator_codes or list(INDICATORS)
    years = years or DEFAULT_YEARS

    dataflow = get_datastructures()
    territory_ids = extract_district_codes_only(dataflow)

    # подготовим структуры последовательно, чтобы потоки не писали один и тот же кэш
    for code in indicator_codes:
        _structure(code)

    tasks = [(code, year) for code in indicator_codes for year in years]

    def run(task):
        code, year = task
        try:
            return task, fetch_indicator_year(code, year, territory_ids)
        except Exception as e:
            print(f'[indicators] {code} {year}: {e}')
            return task, []

    records: List[IndicatorRecord] = []
    with ThreadPoolExecutor(max_workers=workers) as pool:
        for (code, year), part in pool.map(run, tasks):
            print(f'[indicators] {code} {INDICATORS[code][0]} {year}: {len(part)} values')
            records.extend(part)

    stats = merge_regional_cities(records, build_population_weights())
    print(f"[indicators] regional cities merged into districts: {stats['merged']} values, skipped: {stats['skipped']}")

    return records
