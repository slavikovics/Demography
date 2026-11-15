"""Прогнозы дополнительных показателей (рождаемость, смертность, миграция и т.д.).

Три модели, как и для населения: prophet, linear, exponential.
Модель обучается на всех годах, где у Белстата есть данные (для районного уровня
естественного движения и миграции нет 2020–2023), и строит прогноз от последнего
года данных до TARGET_YEAR.

Вычисления идут в процессах (Prophet нагружает CPU), запись в БД выполняется
один раз из основного процесса.
"""
import logging
import warnings
from concurrent.futures import ProcessPoolExecutor
from typing import Dict, List, Optional, Tuple

import numpy as np
import pandas as pd

from indicator_catalog import FORECAST_END_YEAR, INDICATORS, SIGNED_CODES
from data_storage.database import DemographyDatabase
from models.indicator_record import IndicatorRecord

TARGET_YEAR = FORECAST_END_YEAR
MODEL_TYPES = ['prophet', 'linear', 'exponential']
MIN_POINTS = 3

# коэффициенты и плотность — округляем до 0.1, остальное — до целых
FLOAT_CODES = {code for code, (key, _, _) in INDICATORS.items()
               if key.endswith('_per_1000') or key == 'population_density'}


def _prophet(years: List[int], values: List[float], horizon: List[int]) -> List[float]:
    logging.getLogger('cmdstanpy').setLevel(logging.ERROR)
    logging.getLogger('prophet').setLevel(logging.ERROR)
    from prophet import Prophet

    df = pd.DataFrame({'ds': pd.to_datetime([f'{y}-01-01' for y in years]), 'y': values})
    model = Prophet(yearly_seasonality=False, weekly_seasonality=False, daily_seasonality=False,
                    changepoint_prior_scale=0.05)
    model.fit(df)
    future = pd.DataFrame({'ds': pd.to_datetime([f'{y}-01-01' for y in horizon])})
    return list(model.predict(future)['yhat'])


def _linear(years: List[int], values: List[float], horizon: List[int]) -> List[float]:
    from sklearn.linear_model import LinearRegression

    model = LinearRegression().fit(np.array(years).reshape(-1, 1), np.array(values))
    return list(model.predict(np.array(horizon).reshape(-1, 1)))


def _exponential(years: List[int], values: List[float], horizon: List[int]) -> List[float]:
    from statsmodels.tsa.holtwinters import ExponentialSmoothing

    # ETS требует равномерный ряд: пропущенные годы (например, 2020–2023)
    # заполняются линейной интерполяцией — только для этой модели
    full_years = list(range(min(years), max(years) + 1))
    series = np.interp(full_years, years, values)

    try:
        fit = ExponentialSmoothing(series, trend='add', seasonal=None,
                                   initialization_method='estimated').fit()
        return list(fit.forecast(len(horizon)))
    except Exception:
        return [float(np.mean(series))] * len(horizon)


_MODELS = {'prophet': _prophet, 'linear': _linear, 'exponential': _exponential}


def _forecast_task(task: tuple) -> Tuple[tuple, Optional[List[tuple]], Optional[str]]:
    """task = (territory_id, code, unit, model, years, values). Возвращает строки для БД."""
    territory_id, code, unit, model, years, values = task
    warnings.filterwarnings('ignore')
    try:
        last_year = max(years)
        horizon = list(range(last_year + 1, TARGET_YEAR + 1))
        if not horizon:
            return task[:4], [], None

        predicted = _MODELS[model](years, values, horizon)

        rows = []
        for year, value in zip(horizon, predicted):
            value = float(value)
            if code not in SIGNED_CODES:
                value = max(value, 0.0)
            value = round(value, 1) if code in FLOAT_CODES else float(round(value))
            rows.append((territory_id, code, year, value, unit, model))
        return task[:4], rows, None
    except Exception as e:
        return task[:4], None, str(e)


def load_series(db: DemographyDatabase, codes=None) -> Dict[tuple, tuple]:
    """{(territory_id, code): (unit, years, values)} из исторических данных."""
    series: Dict[tuple, tuple] = {}
    for code in codes or INDICATORS:
        for territory_id in db.get_indicator_territory_ids(code):
            rows = db.get_indicator_series(code, territory_id, 'historical')
            if len(rows) < MIN_POINTS:
                continue
            years = [r[2] for r in rows]
            values = [r[3] for r in rows]
            series[(territory_id, code)] = (rows[0][4], years, values)

    # упразднённые территории (ряд закончился задолго до последнего года данных) не прогнозируем
    latest = {}
    for (territory_id, code), (_, years, _) in series.items():
        latest[code] = max(latest.get(code, 0), max(years))
    return {key: value for key, value in series.items() if max(value[1]) >= latest[key[1]] - 1}


def build_indicator_forecasts(db_path: str = 'demography.db', codes=None, model_types=None,
                              workers: Optional[int] = None) -> int:
    db = DemographyDatabase(db_path)
    model_types = model_types or MODEL_TYPES
    series = load_series(db, codes)

    tasks = [(territory_id, code, unit, model, years, values)
             for (territory_id, code), (unit, years, values) in series.items()
             for model in model_types]

    print(f'Indicator forecasts: {len(series)} series x {len(model_types)} models = {len(tasks)} tasks')

    rows: List[tuple] = []
    failed = 0
    done = 0

    with ProcessPoolExecutor(max_workers=workers) as pool:
        for key, part, error in pool.map(_forecast_task, tasks, chunksize=8):
            done += 1
            if error is not None:
                failed += 1
                if failed <= 10:
                    print(f'[indicator forecast] failed {key}: {error}')
            else:
                rows.extend(part)
            if done % 500 == 0:
                print(f'[indicator forecast] {done}/{len(tasks)}')

    db.insert_indicator_records(rows)
    print(f'Indicator forecasts done: {len(rows)} values saved, {failed} failed tasks')
    return len(rows)


if __name__ == '__main__':
    build_indicator_forecasts()
