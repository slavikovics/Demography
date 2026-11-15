"""Доступ к demography.db только для чтения и справочная информация о территориях."""
import difflib
import os
import re
import sqlite3
import threading
from pathlib import Path
from typing import Dict, List, Optional

from indicator_catalog import (
    ADDITIVE_CODES, BELARUS_ID, DENSITY_CODE, FORECAST_MODELS, INDICATORS, LAST_HISTORICAL_INDICATOR_YEAR,
    LAST_HISTORICAL_POPULATION_YEAR, MINSK_ID, RATE_CODES, REGIONAL_CITY_PAIRS, SIGNED_CODES, indicator_group,
)

POPULATION = 'population'

DEFAULT_DB = Path(__file__).resolve().parent.parent / 'demography.db'

# показатель «на 1000 человек» -> абсолютный показатель, из которого он считается
RATE_BASE = {
    '10101200002': '10101200001',
    '10101200004': '10101200003',
    '10101200009': '10101200008',
    '10101200015': '10101200014',
    '10101200017': '10101200016',
}

GENDERS = {'total': 'Total', 'male': 'Males', 'female': 'Females'}


class ToolInputError(ValueError):
    """Ошибка аргументов инструмента: сообщение показывается модели и должно подсказывать, как исправить вызов."""


def last_historical_year(indicator: str) -> int:
    return LAST_HISTORICAL_POPULATION_YEAR if indicator == POPULATION else LAST_HISTORICAL_INDICATOR_YEAR


def db_path() -> str:
    return os.getenv('DEMOGRAPHY_DB') or str(DEFAULT_DB)


def connect() -> sqlite3.Connection:
    """Новое соединение только для чтения (на каждый вызов — безопасно для потоков)."""
    path = db_path()
    if not Path(path).exists():
        raise FileNotFoundError(f'База данных не найдена: {path}. Сначала загрузите данные (python -m prepare).')
    conn = sqlite3.connect(f'file:{path}?mode=ro', uri=True, timeout=10)
    conn.execute('PRAGMA query_only = ON')
    return conn


def _normalize(text: str) -> str:
    text = (text or '').lower().replace('ё', 'е')
    text = re.sub(r'\b(район|района|районе|районы|р-н|область|области|обл|город|города|г|city|district|region|town|of)\b', ' ', text)
    text = re.sub(r'[^\w\s-]', ' ', text)
    return re.sub(r'\s+', ' ', text).strip()


def _stems(text: str) -> List[str]:
    # основа слова: первые 6 символов («Барановичский» ≈ «Барановичи» ≈ «Барановичском»)
    return [word[:6] for word in _normalize(text).split() if len(word) >= 3]


class Territories:
    """Справочник территорий с уровнями (республика / область / район / город / Минск)."""

    def __init__(self, conn: sqlite3.Connection):
        rows = conn.execute('SELECT id, name_ru, name_en, parent_id FROM territories').fetchall()
        raw = {r[0]: {'id': r[0], 'name_ru': (r[1] or '').replace('"', ''), 'name_en': (r[2] or '').replace('"', ''),
                      'parent_id': r[3]} for r in rows}

        # территории, у которых есть данные в последние годы (упразднённые скрываем)
        active = {r[0] for r in conn.execute(
            "SELECT DISTINCT territory_id FROM population WHERE model='historical' AND year >= ? "
            "UNION SELECT DISTINCT territory_id FROM indicators WHERE model='historical' AND year >= ?",
            (LAST_HISTORICAL_POPULATION_YEAR - 1, LAST_HISTORICAL_POPULATION_YEAR - 1))}

        oblast_ids = {t['id'] for t in raw.values() if t['parent_id'] == BELARUS_ID and t['id'] != MINSK_ID}
        city_to_district = dict(REGIONAL_CITY_PAIRS)
        district_to_city = {district: city for city, district in REGIONAL_CITY_PAIRS}

        self.items: Dict[int, dict] = {}
        for tid, t in raw.items():
            if tid == BELARUS_ID:
                level, oblast = 'republic', None
            elif tid == MINSK_ID:
                level, oblast = 'minsk', tid
            elif tid in oblast_ids:
                level, oblast = 'oblast', tid
            elif tid in active and t['parent_id'] in oblast_ids:
                level = 'city' if tid in city_to_district else 'district'
                oblast = t['parent_id']
            else:
                continue  # не относится к иерархии данных (упразднённые, прочие)
            item = {**t, 'level': level, 'oblast_id': oblast, 'has_data': tid in active}
            if tid in district_to_city:
                city = raw[district_to_city[tid]]
                item['includes_city'] = {'id': city['id'], 'name_ru': city['name_ru'], 'name_en': city['name_en']}
            if tid in city_to_district:
                item['merged_into_district_id'] = city_to_district[tid]
            self.items[tid] = item

        self.oblasts = {tid: t for tid, t in self.items.items() if t['level'] == 'oblast'}
        self._index = {tid: (_normalize(t['name_ru']), _normalize(t['name_en']), _stems(t['name_ru']), _stems(t['name_en']))
                       for tid, t in self.items.items()}

    def get(self, territory_id: int) -> dict:
        try:
            return self.items[int(territory_id)]
        except (KeyError, ValueError, TypeError):
            raise ToolInputError(
                f'Территория {territory_id} не найдена. Найдите id через search_territories(query).') from None

    def label(self, territory_id: int) -> str:
        item = self.items.get(territory_id)
        return item['name_ru'] if item else str(territory_id)

    def public(self, item: dict) -> dict:
        out = {'id': item['id'], 'name_ru': item['name_ru'], 'name_en': item['name_en'], 'level': item['level']}
        if item['oblast_id'] and item['oblast_id'] != item['id']:
            out['oblast'] = self.items[item['oblast_id']]['name_ru']
        if 'includes_city' in item:
            out['includes_city'] = item['includes_city']['name_ru']
        if item['level'] == 'city':
            out['note'] = 'город областного подчинения; его значения уже входят в значения соседнего района'
        if item['level'] == 'oblast':
            out['note'] = 'у области нет собственных рядов: итоги считаются как сумма районов (region_totals, get_series)'
        return out

    def search(self, query: str, limit: int = 10) -> List[dict]:
        q_norm, q_stems = _normalize(query), _stems(query)
        if not q_norm:
            raise ToolInputError('Пустой запрос: укажите название района, города или области.')

        scored = []
        for tid, (ru, en, ru_stems, en_stems) in self._index.items():
            score = 0.0
            if q_norm in (ru, en):
                score = 100
            elif q_stems and all(s in ru_stems or s in en_stems for s in q_stems):
                score = 80 + 10 * (len(q_stems) / max(len(ru_stems), 1))
            elif q_norm in ru or q_norm in en:
                score = 60
            else:
                ratio = max(difflib.SequenceMatcher(None, q_norm, ru).ratio(), difflib.SequenceMatcher(None, q_norm, en).ratio())
                score = ratio * 50 if ratio >= 0.62 else 0
            if score:
                # при равенстве предпочитаем районы и области городам
                bonus = {'district': 1.0, 'minsk': 0.9, 'oblast': 0.8, 'republic': 0.7, 'city': 0.5}[self.items[tid]['level']]
                scored.append((score + bonus, tid))
        scored.sort(key=lambda pair: -pair[0])
        return [self.public(self.items[tid]) for _, tid in scored[:limit]]

    def districts(self, oblast_id: Optional[int] = None) -> List[int]:
        return [tid for tid, t in self.items.items()
                if t['level'] == 'district' and (oblast_id is None or t['oblast_id'] == oblast_id)]

    def resolve_oblast(self, value) -> int:
        """Область по id или названию («Гомельская», «Gomel»)."""
        if isinstance(value, int) or (isinstance(value, str) and value.strip().isdigit()):
            item = self.get(int(value))
            if item['level'] not in ('oblast', 'minsk'):
                raise ToolInputError(f'{item["name_ru"]} не область. Укажите область или оставьте параметр пустым.')
            return item['id']
        found = [t for t in self.search(str(value), 5) if t['level'] in ('oblast', 'minsk')]
        if not found:
            names = ', '.join(t['name_ru'] for t in self.oblasts.values())
            raise ToolInputError(f'Область «{value}» не найдена. Доступны: {names}, г. Минск.')
        return found[0]['id']


_lock = threading.Lock()
_cache: Dict[str, Territories] = {}


def territories() -> Territories:
    """Справочник территорий (кэш на процесс; перезагружается при смене файла БД)."""
    path = db_path()
    mtime = str(os.path.getmtime(path)) if Path(path).exists() else ''
    key = f'{path}:{mtime}'
    with _lock:
        if key not in _cache:
            _cache.clear()
            conn = connect()
            try:
                _cache[key] = Territories(conn)
            finally:
                conn.close()
        return _cache[key]


def indicator_meta(code: str) -> dict:
    key, name_ru, name_en = INDICATORS[code]
    return {'code': code, 'key': key, 'name_ru': name_ru, 'name_en': name_en}


def resolve_indicator(value: str) -> str:
    """Принимает код, ключ (births), 'population' или название; возвращает код показателя."""
    text = str(value).strip()
    if text.lower() in (POPULATION, 'население', 'численность населения', 'population'):
        return POPULATION
    if text in INDICATORS:
        return text
    for code, (key, name_ru, name_en) in INDICATORS.items():
        if text.lower() in (key.lower(), name_ru.lower(), name_en.lower()):
            return code
    norm = text.lower()
    candidates = [code for code, (key, name_ru, name_en) in INDICATORS.items()
                  if norm in name_ru.lower() or norm in name_en.lower() or norm in key]
    if len(candidates) == 1:
        return candidates[0]
    similar = candidates or [c for c, (k, ru, en) in INDICATORS.items()
                             if difflib.SequenceMatcher(None, norm, ru.lower()).ratio() > 0.45][:5]
    hint = '; '.join(f'{c} — {INDICATORS[c][1]}' for c in similar) if similar else 'вызовите list_indicators()'
    raise ToolInputError(f'Неизвестный показатель «{value}». Похожие: {hint}.')


__all__ = [
    'ADDITIVE_CODES', 'DENSITY_CODE', 'FORECAST_MODELS', 'GENDERS', 'INDICATORS', 'POPULATION', 'RATE_BASE', 'RATE_CODES',
    'SIGNED_CODES', 'ToolInputError', 'Territories', 'connect', 'db_path', 'indicator_group', 'indicator_meta',
    'last_historical_year', 'resolve_indicator', 'territories',
]
