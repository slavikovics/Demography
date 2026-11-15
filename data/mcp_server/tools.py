"""Инструменты демографической статистики. Чистые функции: принимают аргументы и возвращают JSON-совместимые dict.

Правила для всех ответов: числа — как в БД (без округления «для красоты»), всегда есть единица измерения,
год и источник («belstat» — опубликованные данные, «forecast:<model>» — прогноз), проблемы данных — в `notes`.
"""
import re
import sqlite3
import statistics
import time
from typing import Dict, List, Optional, Sequence

from indicator_catalog import FORECAST_END_YEAR
from mcp_server.store import (
    ADDITIVE_CODES, DENSITY_CODE, FORECAST_MODELS, GENDERS, INDICATORS, POPULATION, RATE_BASE, RATE_CODES,
    SIGNED_CODES, ToolInputError, connect, indicator_group, indicator_meta, last_historical_year,
    resolve_indicator, territories,
)

MODELS = ('historical',) + FORECAST_MODELS
MAX_TERRITORIES = 10
MAX_ROWS = 200
MIN_YEAR = 2010

METHODOLOGY_NOTES = [
    'Источник: Национальный статистический комитет Республики Беларусь (Белстат).',
    'Города областного подчинения (Барановичи, Брест, Пинск, Витебск, Новополоцк, Гомель, Гродно, Жодино, Бобруйск, '
    'Могилёв) уже включены в значения соседнего района: значение «Брестского района» — это район вместе с г. Брестом. '
    'Отдельные строки городов тоже есть, но складывать их с районами нельзя (двойной счёт).',
    'Области как отдельные территории в данных не хранятся: их итоги считаются суммой районов (region_totals).',
    'Естественное движение и миграция по районам за 2020–2023 годы Белстат не публикует — этих лет в данных нет.',
    'Прогнозы (prophet, linear, exponential) — это экстраполяция тренда на коротком ряде, а не демографическая '
    'проекция; модели сильно расходятся к 2034 году. Всегда называйте модель и предупреждайте, что это прогноз.',
]


# ---------------------------------------------------------------------------------------------- вспомогательное

def _num(value):
    """Целые значения — без «.0», дробные — как есть (округление до 3 знаков убирает артефакты float)."""
    if value is None:
        return None
    value = float(value)
    return int(value) if value.is_integer() else round(value, 3)


def _unit(code: str, conn: sqlite3.Connection) -> str:
    if code == POPULATION:
        return 'чел.'
    row = conn.execute('SELECT unit FROM indicators WHERE indicator_code = ? AND unit IS NOT NULL LIMIT 1', (code,)).fetchone()
    return row[0] if row else ''


def _indicator_header(code: str, conn: sqlite3.Connection) -> dict:
    if code == POPULATION:
        return {'code': POPULATION, 'name_ru': 'Численность населения (среднегодовая)',
                'name_en': 'Population (annual average)', 'unit': 'чел.', 'signed': False}
    return {**indicator_meta(code), 'unit': _unit(code, conn), 'signed': code in SIGNED_CODES}


def _check_model(model: str) -> str:
    if model not in MODELS:
        raise ToolInputError(f'Неизвестная модель «{model}». Допустимо: {", ".join(MODELS)}.')
    return model


def _check_gender(code: str, gender: str) -> str:
    gender = (gender or 'total').lower()
    if gender not in GENDERS:
        raise ToolInputError('gender: допустимо total, male, female.')
    if code != POPULATION and gender != 'total':
        raise ToolInputError('Разбивка по полу доступна только для показателя population; для остальных используйте gender=total.')
    return gender


def _check_years(year_from: Optional[int], year_to: Optional[int]) -> tuple:
    year_from = MIN_YEAR if year_from is None else int(year_from)
    year_to = FORECAST_END_YEAR if year_to is None else int(year_to)
    if year_from > year_to:
        raise ToolInputError(f'year_from ({year_from}) больше year_to ({year_to}).')
    if year_to < MIN_YEAR or year_from > FORECAST_END_YEAR:
        raise ToolInputError(f'Данные охватывают {MIN_YEAR}–{FORECAST_END_YEAR}.')
    return max(year_from, MIN_YEAR), min(year_to, FORECAST_END_YEAR)


def _fetch(conn: sqlite3.Connection, code: str, model: str, year_from: int, year_to: int,
           territory_ids: Optional[Sequence[int]] = None, gender: str = 'total') -> List[tuple]:
    """Строки (territory_id, year, value) для показателя и модели."""
    params: list = []
    if code == POPULATION:
        sql = ("SELECT territory_id, year, people FROM population WHERE model = ? AND gender = ? "
               "AND age_group = 'By all age' AND year BETWEEN ? AND ?")
        params += [model, GENDERS[gender], year_from, year_to]
    else:
        sql = "SELECT territory_id, year, value FROM indicators WHERE indicator_code = ? AND model = ? AND year BETWEEN ? AND ?"
        params += [code, model, year_from, year_to]
    if territory_ids is not None:
        marks = ','.join('?' * len(territory_ids))
        sql += f' AND territory_id IN ({marks})'
        params += list(territory_ids)
    return conn.execute(sql, params).fetchall()


def _available_years(conn: sqlite3.Connection, code: str, model: str = 'historical') -> List[int]:
    if code == POPULATION:
        rows = conn.execute("SELECT DISTINCT year FROM population WHERE model = ? ORDER BY year", (model,)).fetchall()
    else:
        rows = conn.execute("SELECT DISTINCT year FROM indicators WHERE indicator_code = ? AND model = ? ORDER BY year",
                            (code, model)).fetchall()
    return [r[0] for r in rows]


def _compress(years: Sequence[int]) -> str:
    """[2010,2011,2012,2024] -> '2010–2012, 2024'."""
    years = sorted(years)
    parts, start, prev = [], None, None
    for y in years:
        if start is None:
            start = prev = y
        elif y == prev + 1:
            prev = y
        else:
            parts.append(f'{start}–{prev}' if start != prev else str(start))
            start = prev = y
    if start is not None:
        parts.append(f'{start}–{prev}' if start != prev else str(start))
    return ', '.join(parts)


def _effective_model(conn: sqlite3.Connection, code: str, year: int, model: str, notes: List[str]) -> str:
    """Какую модель реально читать для года. Факты за прошлые годы всегда берутся из исторических данных."""
    _check_model(model)
    last = last_historical_year(code)
    if model == 'historical':
        if year > last:
            raise ToolInputError(
                f'За {year} год нет опубликованных данных (последний — {last}). '
                f'Для будущих лет укажите model: {", ".join(FORECAST_MODELS)} (это прогноз).')
        return 'historical'
    if year <= last:
        notes.append(f'За {year} год есть опубликованные данные, поэтому использованы они, а не прогноз модели {model}.')
        return 'historical'
    return model


def _source(model: str) -> str:
    return 'belstat' if model == 'historical' else f'forecast:{model}'


def _no_data_error(conn: sqlite3.Connection, code: str, year: int, model: str) -> ToolInputError:
    have = _available_years(conn, code, model)
    return ToolInputError(f'Нет данных за {year} год (model={model}). Доступные годы: {_compress(have) or "нет"}.')


# ----------------------------------------------------------------------- агрегирование районов в области

def _aggregate_by_oblast(conn, code: str, model: str, year_from: int, year_to: int, gender: str,
                         notes: List[str]) -> Dict[int, Dict[int, float]]:
    """{oblast_id: {year: value}} — суммы по районам (города областного подчинения не учитываются: они уже в районах)."""
    terr = territories()
    district_oblast = {tid: terr.items[tid]['oblast_id'] for tid in terr.districts()}

    def sums(indicator: str, y0: int, y1: int, sum_gender: str) -> Dict[int, Dict[int, float]]:
        totals: Dict[int, Dict[int, float]] = {}
        for tid, year, value in _fetch(conn, indicator, model, y0, y1, list(district_oblast), sum_gender):
            bucket = totals.setdefault(district_oblast[tid], {})
            bucket[year] = bucket.get(year, 0.0) + value
        return totals

    if code == DENSITY_CODE:
        raise ToolInputError('Плотность населения нельзя просуммировать по областям. Используйте rank_territories '
                             'с параметром oblast или get_series по районам.')
    if code == POPULATION or code in ADDITIVE_CODES:
        return sums(code, year_from, year_to, gender)

    # коэффициенты «на 1000»: сумма абсолютных значений / население * 1000
    base = RATE_BASE[code]
    base_sums = sums(base, year_from, year_to, 'total')
    pop_sums = sums(POPULATION, year_from, year_to, 'total')
    if model == 'historical' and year_to > 2024:
        pop_last = sums(POPULATION, 2024, 2024, 'total')
        for oblast, years in base_sums.items():
            for year in years:
                if year > 2024 and year not in pop_sums.get(oblast, {}):
                    pop_sums.setdefault(oblast, {})[year] = pop_last.get(oblast, {}).get(2024, 0.0)
        notes.append('Для 2025 года население недоступно: при расчёте коэффициентов использовано население 2024 года.')
    notes.append('Коэффициенты по областям пересчитаны как сумма абсолютных значений по районам / население * 1000.')
    result: Dict[int, Dict[int, float]] = {}
    for oblast, years in base_sums.items():
        for year, value in years.items():
            population = pop_sums.get(oblast, {}).get(year)
            if population:
                result.setdefault(oblast, {})[year] = round(value / population * 1000, 1)
    return result


def _series_for(conn, code: str, territory: dict, model: str, year_from: int, year_to: int, gender: str,
                notes: List[str]) -> Dict[int, float]:
    if territory['level'] == 'oblast':
        return _aggregate_by_oblast(conn, code, model, year_from, year_to, gender, notes).get(territory['id'], {})
    rows = _fetch(conn, code, model, year_from, year_to, [territory['id']], gender)
    return {year: value for _, year, value in rows}


# ----------------------------------------------------------------------------------------------- инструменты

def list_indicators() -> dict:
    """Каталог доступных показателей с годами данных, единицами и особенностями."""
    conn = connect()
    try:
        entries = []
        for code in [POPULATION] + list(INDICATORS):
            header = _indicator_header(code, conn)
            historical = _available_years(conn, code, 'historical')
            forecast = {}
            for model in FORECAST_MODELS:
                years = _available_years(conn, code, model)
                if years:
                    forecast[model] = _compress(years)
            first, last = (historical[0], historical[-1]) if historical else (None, None)
            gaps = [y for y in range(first, last + 1) if y not in historical] if historical else []
            entry = {
                **header,
                'group': indicator_group(code) if code != POPULATION else 'population',
                'historical_years': _compress(historical),
                'missing_years': _compress(gaps) if gaps else None,
                'forecast_years': forecast,
                'type': ('rate_per_1000' if code in RATE_CODES else 'density' if code == DENSITY_CODE else
                         'count' if code in ADDITIVE_CODES or code == POPULATION else 'other'),
                'aggregatable_to_oblast': code != DENSITY_CODE,
            }
            if code == POPULATION:
                entry['genders'] = ['total', 'male', 'female']
            entries.append(entry)
        return {'indicators': entries, 'forecast_models': list(FORECAST_MODELS), 'notes': METHODOLOGY_NOTES}
    finally:
        conn.close()


def search_territories(query: str, limit: int = 10) -> dict:
    """Нечёткий поиск территории по названию (рус./англ.), падежи и «район/область» не мешают."""
    limit = max(1, min(int(limit), 25))
    found = territories().search(query, limit)
    result = {'query': query, 'results': found}
    if not found:
        result['hint'] = 'Ничего не найдено. Попробуйте основу названия (например, «Барано») или английское написание.'
    return result


def get_series(indicator: str, territory_ids: List[int], year_from: Optional[int] = None, year_to: Optional[int] = None,
               models: Optional[List[str]] = None, gender: str = 'total') -> dict:
    """Ряды значений по годам для одной или нескольких территорий (до 10)."""
    code = resolve_indicator(indicator)
    gender = _check_gender(code, gender)
    year_from, year_to = _check_years(year_from, year_to)
    models = models or ['historical']
    for model in models:
        _check_model(model)
    if not territory_ids:
        raise ToolInputError('Укажите territory_ids (id из search_territories), до 10 штук. Республика: 699961.')
    if len(territory_ids) > MAX_TERRITORIES:
        raise ToolInputError(f'Слишком много территорий ({len(territory_ids)}), максимум {MAX_TERRITORIES}. '
                             'Для сравнения многих районов используйте rank_territories.')

    terr = territories()
    conn = connect()
    try:
        notes: List[str] = []
        series, missing = [], []
        for territory_id in dict.fromkeys(int(t) for t in territory_ids):
            territory = terr.get(territory_id)
            for model in dict.fromkeys(models):
                data = _series_for(conn, code, territory, model, year_from, year_to, gender, notes)
                if not data:
                    missing.append({'territory': territory['name_ru'], 'model': model})
                    continue
                entry = {
                    'territory': {'id': territory['id'], 'name_ru': territory['name_ru'], 'level': territory['level']},
                    'model': model,
                    'source': _source(model),
                    'points': {str(y): _num(v) for y, v in sorted(data.items())},
                }
                if territory['level'] == 'oblast':
                    entry['aggregated'] = 'сумма по районам области'
                if 'includes_city' in territory:
                    entry['includes_city'] = territory['includes_city']['name_ru']
                series.append(entry)

        if missing:
            have = _compress(_available_years(conn, code, 'historical'))
            notes.append(f'Нет данных для: {", ".join(f"{m["territory"]} ({m["model"]})" for m in missing)}. '
                         f'Опубликованные годы: {have}.')
        if any(m != 'historical' for m in models):
            notes.append('Прогнозные значения — экстраполяция тренда выбранной модели, не официальные данные.')
        header = _indicator_header(code, conn)
        if code == POPULATION:
            header['gender'] = gender
        return {'indicator': header, 'series': series, 'notes': list(dict.fromkeys(notes))}
    finally:
        conn.close()


def _scope_ids(scope: str, oblast_id: Optional[int]) -> List[int]:
    terr = territories()
    levels = {'districts': ('district',), 'cities': ('city', 'minsk'), 'all': ('district', 'city', 'minsk')}
    if scope not in levels:
        raise ToolInputError('scope: допустимо districts (районы, по умолчанию), cities (города областного подчинения и Минск), all.')
    return [tid for tid, t in terr.items.items()
            if t['level'] in levels[scope] and (oblast_id is None or t['oblast_id'] == oblast_id)]


def _values_for_year(conn, code: str, model: str, year: int, ids: Sequence[int], gender: str) -> Dict[int, float]:
    return {tid: value for tid, _, value in _fetch(conn, code, model, year, year, list(ids), gender)}


def _label_row(terr, tid: int, value, **extra) -> dict:
    item = terr.items[tid]
    row = {'id': tid, 'name_ru': item['name_ru'], 'name_en': item['name_en'], 'value': _num(value)}
    if item['level'] == 'city':
        row['level'] = 'city'
    if item['oblast_id'] and item['oblast_id'] != tid:
        row['oblast'] = terr.items[item['oblast_id']]['name_ru']
    row.update(extra)
    return row


def rank_territories(indicator: str, year: int, model: str = 'historical', top_n: int = 10, order: str = 'desc',
                     oblast: Optional[str] = None, scope: str = 'districts', gender: str = 'total') -> dict:
    """Рейтинг территорий по показателю за год (с республикой, средним и медианой для контекста)."""
    code = resolve_indicator(indicator)
    gender = _check_gender(code, gender)
    top_n = max(1, min(int(top_n), 50))
    if order not in ('asc', 'desc'):
        raise ToolInputError('order: asc (по возрастанию) или desc (по убыванию).')
    year = int(year)

    terr = territories()
    conn = connect()
    try:
        notes: List[str] = []
        used_model = _effective_model(conn, code, year, model, notes)
        oblast_id = terr.resolve_oblast(oblast) if oblast not in (None, '') else None
        ids = _scope_ids(scope, oblast_id)
        values = _values_for_year(conn, code, used_model, year, ids, gender)
        if not values:
            raise _no_data_error(conn, code, year, used_model)

        ordered = sorted(values.items(), key=lambda kv: kv[1], reverse=(order == 'desc'))
        rows = [_label_row(terr, tid, value, rank=i + 1) for i, (tid, value) in enumerate(ordered[:top_n])]
        everything = list(values.values())
        republic = _values_for_year(conn, code, used_model, year, [699961], gender).get(699961)
        context = {'count': len(values), 'mean': _num(round(statistics.fmean(everything), 3)),
                   'median': _num(statistics.median(everything)), 'min': _num(min(everything)), 'max': _num(max(everything)),
                   'republic': _num(republic)}
        if code in RATE_CODES or code == DENSITY_CODE:
            notes.append('Среднее и медиана считаются по территориям без весов (простое среднее значений районов).')
        if used_model != 'historical':
            notes.append('Прогнозные значения — экстраполяция тренда модели, не официальные данные.')
        if scope == 'districts':
            notes.append('Значения районов включают города областного подчинения; Минск в рейтинг районов не входит (scope=cities или all).')
        return {
            'indicator': _indicator_header(code, conn), 'year': year, 'model': used_model, 'source': _source(used_model),
            'order': order, 'scope': scope, 'oblast': terr.items[oblast_id]['name_ru'] if oblast_id else None,
            'rows': rows, 'context': context, 'notes': list(dict.fromkeys(notes)),
        }
    finally:
        conn.close()


def compare_years(indicator: str, year_from: int, year_to: int, model: str = 'historical', top_n: int = 10,
                  territory_ids: Optional[List[int]] = None, scope: str = 'districts', gender: str = 'total') -> dict:
    """Изменение показателя между двумя годами: лидеры роста и падения (или выбранные территории)."""
    code = resolve_indicator(indicator)
    gender = _check_gender(code, gender)
    year_from, year_to = int(year_from), int(year_to)
    if year_from == year_to:
        raise ToolInputError('year_from и year_to должны различаться.')
    top_n = max(1, min(int(top_n), 50))

    terr = territories()
    conn = connect()
    try:
        notes: List[str] = []
        model_from = _effective_model(conn, code, year_from, model, notes)
        model_to = _effective_model(conn, code, year_to, model, notes)
        if territory_ids:
            if len(territory_ids) > 25:
                raise ToolInputError('territory_ids: не более 25 территорий.')
            ids = [terr.get(int(t))['id'] for t in territory_ids]
        else:
            ids = _scope_ids(scope, None) + [699961]
        before = _values_for_year(conn, code, model_from, year_from, ids, gender)
        after = _values_for_year(conn, code, model_to, year_to, ids, gender)
        both = [tid for tid in ids if tid in before and tid in after]
        if not both:
            missing_year = year_from if not before else year_to
            raise _no_data_error(conn, code, missing_year, model_from if not before else model_to)

        def make(tid: int) -> dict:
            a, b = before[tid], after[tid]
            return _label_row(terr, tid, b, value_from=_num(a), value_to=_num(b), change=_num(round(b - a, 3)),
                              change_percent=_num(round((b - a) / a * 100, 2)) if a else None)

        rows = [make(tid) for tid in both]
        republic = next((r for r in rows if r['id'] == 699961), None)
        rows = [r for r in rows if r['id'] != 699961]
        by_change = sorted(rows, key=lambda r: r['change'], reverse=True)
        result = {
            'indicator': _indicator_header(code, conn), 'year_from': year_from, 'year_to': year_to,
            'source_from': _source(model_from), 'source_to': _source(model_to), 'republic': republic, 'compared': len(rows),
        }
        if territory_ids:
            result['rows'] = by_change
        else:
            result['top_growth'] = by_change[:top_n]
            result['top_decline'] = list(reversed(by_change[-top_n:]))
        if code in RATE_CODES or code == DENSITY_CODE:
            notes.append('Для коэффициентов изменение (change) — разность значений в тех же единицах, а не проценты.')
        if 'forecast' in _source(model_to) or 'forecast' in _source(model_from):
            notes.append('Прогнозные значения — экстраполяция тренда модели, не официальные данные.')
        result['notes'] = list(dict.fromkeys(notes))
        return result
    finally:
        conn.close()


def region_totals(indicator: str, year: int, model: str = 'historical', gender: str = 'total') -> dict:
    """Итоги по областям, г. Минску и республике за год."""
    code = resolve_indicator(indicator)
    gender = _check_gender(code, gender)
    year = int(year)
    terr = territories()
    conn = connect()
    try:
        notes: List[str] = []
        used_model = _effective_model(conn, code, year, model, notes)
        by_oblast = _aggregate_by_oblast(conn, code, used_model, year, year, gender, notes)
        direct = _values_for_year(conn, code, used_model, year, [699961, 919071], gender)
        if not by_oblast and not direct:
            raise _no_data_error(conn, code, year, used_model)

        rows = []
        for oblast_id, item in terr.oblasts.items():
            value = by_oblast.get(oblast_id, {}).get(year)
            if value is not None:
                rows.append({'id': oblast_id, 'name_ru': item['name_ru'], 'name_en': item['name_en'], 'value': _num(value)})
        if 919071 in direct:
            rows.append({'id': 919071, 'name_ru': 'г. Минск', 'name_en': 'Minsk city', 'value': _num(direct[919071])})
        rows.sort(key=lambda r: r['value'], reverse=True)

        result = {'indicator': _indicator_header(code, conn), 'year': year, 'model': used_model,
                  'source': _source(used_model), 'regions': rows, 'republic': _num(direct.get(699961))}
        if code in ADDITIVE_CODES or code == POPULATION:
            total = sum(r['value'] for r in rows)
            result['sum_of_regions'] = _num(total)
            if direct.get(699961) is not None and abs(total - direct[699961]) > max(1, abs(direct[699961]) * 0.001):
                notes.append(f'Сумма регионов ({_num(total)}) не совпадает со значением по республике ({_num(direct[699961])}): '
                             'расхождение связано с источником данных.')
        if used_model != 'historical':
            notes.append('Прогнозные значения — экстраполяция тренда модели, не официальные данные.')
        result['notes'] = list(dict.fromkeys(notes))
        return result
    finally:
        conn.close()


def territory_profile(territory_id: int, year: int, model: str = 'historical') -> dict:
    """Все показатели одной территории за год (население с разбивкой по полу + показатели)."""
    terr = territories()
    territory = terr.get(int(territory_id))
    year = int(year)
    conn = connect()
    try:
        notes: List[str] = []
        values, missing = [], []
        republic_cache: Dict[tuple, Optional[float]] = {}
        for code in [POPULATION] + list(INDICATORS):
            local_notes: List[str] = []
            try:
                used_model = _effective_model(conn, code, year, model, local_notes)
                header = _indicator_header(code, conn)
                entry = {'code': code, 'name_ru': header['name_ru'], 'unit': header['unit'], 'source': _source(used_model)}
                if code == POPULATION:
                    for gender in ('total', 'male', 'female'):
                        got = _series_for(conn, code, territory, used_model, year, year, gender, local_notes).get(year)
                        entry[gender] = _num(got)
                    if entry['total'] is None:
                        raise ToolInputError('нет данных')
                else:
                    got = _series_for(conn, code, territory, used_model, year, year, 'total', local_notes).get(year)
                    if got is None:
                        raise ToolInputError('нет данных')
                    entry['value'] = _num(got)
                    key = (code, used_model)
                    if key not in republic_cache:
                        republic_cache[key] = _values_for_year(conn, code, used_model, year, [699961], 'total').get(699961)
                    if territory['id'] != 699961 and republic_cache[key] is not None:
                        entry['republic'] = _num(republic_cache[key])
                values.append(entry)
                notes.extend(n for n in local_notes if 'использованы они' in n)
            except ToolInputError:
                missing.append(INDICATORS[code][1] if code in INDICATORS else 'Население')
        if not values:
            raise ToolInputError(f'Для {territory["name_ru"]} нет данных за {year} год (model={model}).')
        if missing:
            notes.append(f'Нет данных за {year} год: {", ".join(missing)}.')
        if model != 'historical' and year > 2024:
            notes.append('Значения за годы после последних опубликованных — прогноз выбранной модели.')
        return {'territory': terr.public(territory), 'year': year, 'model': model, 'values': values,
                'notes': list(dict.fromkeys(notes))}
    finally:
        conn.close()


# ----------------------------------------------------------------------------------------------- read-only SQL

SQL_ALLOWED_TABLES = {'territories', 'population', 'indicators'}
# служебные таблицы SQLite закрыты; имена CTE и подзапросов не являются таблицами и разрешены
SQL_DENIED_TABLES = {'sqlite_master', 'sqlite_schema', 'sqlite_temp_master', 'sqlite_temp_schema', 'sqlite_sequence', 'sqlite_stat1'}
SQL_TIMEOUT_SECONDS = 5.0

SQL_SCHEMA = """\
Таблицы (SQLite):
  territories(id, name_ru, name_en, parent_id)            -- справочник; республика 699961, области — parent_id=699961
  population(territory_id, gender, people, year, age_group, type_of_area, model)
      gender: 'Total'|'Males'|'Females'; age_group всегда 'By all age'; model: 'historical'|'prophet'|'linear'|'exponential'
  indicators(territory_id, indicator_code, year, value, unit, model)
      коды показателей — в list_indicators(); model как выше
Пример: SELECT t.name_ru, i.value FROM indicators i JOIN territories t ON t.id=i.territory_id
        WHERE i.indicator_code='10101200001' AND i.year=2024 AND i.model='historical' ORDER BY i.value DESC LIMIT 5"""


def run_sql(query: str, max_rows: int = 100) -> dict:
    """Один read-only SELECT к таблицам territories / population / indicators. Запасной инструмент."""
    max_rows = max(1, min(int(max_rows), MAX_ROWS))
    text = (query or '').strip().rstrip(';').strip()
    if not text:
        raise ToolInputError('Пустой запрос.')
    if ';' in text:
        raise ToolInputError('Разрешён только один запрос без «;».')
    if not re.match(r'^(select|with)\b', text, re.IGNORECASE):
        raise ToolInputError('Разрешены только запросы SELECT / WITH … SELECT.')

    conn = connect()
    started = time.monotonic()

    def authorizer(action, arg1, arg2, db_name, source):
        if action in (sqlite3.SQLITE_SELECT, sqlite3.SQLITE_FUNCTION, sqlite3.SQLITE_RECURSIVE):
            return sqlite3.SQLITE_OK
        if action == sqlite3.SQLITE_READ and arg1 not in SQL_DENIED_TABLES:
            return sqlite3.SQLITE_OK
        return sqlite3.SQLITE_DENY

    conn.set_authorizer(authorizer)
    conn.set_progress_handler(lambda: 1 if time.monotonic() - started > SQL_TIMEOUT_SECONDS else 0, 50000)
    try:
        cursor = conn.execute(text)
        rows = cursor.fetchmany(max_rows + 1)
        columns = [d[0] for d in cursor.description or []]
    except sqlite3.DatabaseError as e:
        message = str(e)
        if 'not authorized' in message or 'prohibited' in message:
            message = 'Запрос обращается к запрещённым таблицам или операциям. ' + SQL_SCHEMA
        elif 'interrupted' in message:
            message = f'Запрос слишком долгий (>{SQL_TIMEOUT_SECONDS:.0f} с). Добавьте фильтры и LIMIT.'
        raise ToolInputError(f'Ошибка SQL: {message}') from None
    finally:
        conn.close()

    truncated = len(rows) > max_rows
    rows = rows[:max_rows]
    return {'columns': columns, 'rows': [[_num(v) if isinstance(v, float) else v for v in row] for row in rows],
            'row_count': len(rows), 'truncated': truncated,
            'notes': ['Результат обрезан по max_rows.'] if truncated else []}
