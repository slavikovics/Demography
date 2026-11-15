"""Каталог показателей Белстата и константы территорий.

Лёгкий модуль без побочных эффектов (никаких сетевых запросов, чтения файлов
и тяжёлых импортов): его используют и загрузчик данных, и API, и MCP-сервер.
"""
from typing import Dict

BELARUS_ID = 699961
MINSK_ID = 919071

# code -> (ключ, название ru, название en)
INDICATORS: Dict[str, tuple] = {
    '10101100012': ('population_density', 'Плотность населения', 'Population density'),
    '10101200001': ('births', 'Число родившихся', 'Number of births'),
    '10101200002': ('births_per_1000', 'Число родившихся на 1000 человек населения', 'Births per 1000 population'),
    '10101200003': ('deaths', 'Число умерших', 'Number of deaths'),
    '10101200004': ('deaths_per_1000', 'Число умерших на 1000 человек населения', 'Deaths per 1000 population'),
    '10101200008': ('natural_increase', 'Естественный прирост (убыль) населения', 'Natural increase (decrease)'),
    '10101200009': ('natural_increase_per_1000', 'Естественный прирост (убыль) на 1000 человек населения', 'Natural increase (decrease) per 1000 population'),
    '10101200014': ('marriages', 'Число браков', 'Number of marriages'),
    '10101200015': ('marriages_per_1000', 'Число браков на 1000 человек населения', 'Marriages per 1000 population'),
    '10101200016': ('divorces', 'Число разводов', 'Number of divorces'),
    '10101200017': ('divorces_per_1000', 'Число разводов на 1000 человек населения', 'Divorces per 1000 population'),
    '10101300001': ('immigrants', 'Число прибывших лиц', 'Number of arrivals'),
    '10101300002': ('emigrants', 'Число выбывших лиц', 'Number of departures'),
    '10101300003': ('net_migration', 'Миграционный прирост, убыль (-)', 'Net migration'),
}

DENSITY_CODE = '10101100012'

# показатели, которые бывают отрицательными (прирост/убыль)
SIGNED_CODES = {'10101200008', '10101200009', '10101300003'}

# показатели «на 1000 человек населения» — при слиянии усредняются с весом по населению
RATE_CODES = {code for code, (key, _, _) in INDICATORS.items() if key.endswith('_per_1000')}

# абсолютные значения — при слиянии и суммировании по областям складываются
ADDITIVE_CODES = set(INDICATORS) - RATE_CODES - {DENSITY_CODE}

FORECAST_MODELS = ('prophet', 'linear', 'exponential')

# Последний год опубликованных данных: дальше значения — прогноз
LAST_HISTORICAL_POPULATION_YEAR = 2024
LAST_HISTORICAL_INDICATOR_YEAR = 2025
FORECAST_END_YEAR = 2034

# (id города областного подчинения, id района, в который он прибавляется)
REGIONAL_CITY_PAIRS = [
    (919093, 919075),
    (919092, 919077),
    (919094, 919088),
    (919118, 919099),
    (919119, 919108),
    (919145, 919126),
    (919165, 919150),
    (919200, 919193),
    (919225, 919203),
    (919224, 919215),
]

# Темы показателей (как в интерфейсе)
_MARRIAGE_CODES = {'10101200014', '10101200015', '10101200016', '10101200017'}


def indicator_group(code: str) -> str:
    if code in _MARRIAGE_CODES:
        return 'marriage'
    if code.startswith('101012'):
        return 'natural'
    if code.startswith('101013'):
        return 'migration'
    return 'population'
