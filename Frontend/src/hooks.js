import { useCallback, useEffect, useMemo, useState } from 'react';
import { apiUrl, POPULATION } from './config';

// Состояние, которое помнит выбор пользователя между сессиями (если localStorage доступен)
export function usePersistentState(key, initialValue) {
  const [value, setValue] = useState(() => {
    try {
      const stored = window.localStorage.getItem(key);
      return stored !== null ? JSON.parse(stored) : initialValue;
    } catch (e) {
      return initialValue;
    }
  });

  useEffect(() => {
    try {
      window.localStorage.setItem(key, JSON.stringify(value));
    } catch (e) {
      // хранилище недоступно — состояние просто не сохраняется
    }
  }, [key, value]);

  return [value, setValue];
}

// Загрузка JSON с отменой устаревших запросов. 404 — это «нет данных», а не ошибка.
export function useFetchJson(url) {
  const [state, setState] = useState({ data: null, loading: Boolean(url), error: null, status: null });
  const [attempt, setAttempt] = useState(0);

  useEffect(() => {
    if (!url) {
      setState({ data: null, loading: false, error: null, status: null });
      return undefined;
    }

    const controller = new AbortController();
    setState((prev) => ({ ...prev, loading: true, error: null }));

    fetch(url, { signal: controller.signal })
      .then(async (response) => {
        if (response.ok) {
          const data = await response.json();
          setState({ data, loading: false, error: null, status: response.status });
        } else {
          const error = response.status === 404 ? null : new Error(`HTTP ${response.status}`);
          setState({ data: null, loading: false, error, status: response.status });
        }
      })
      .catch((error) => {
        if (error.name === 'AbortError') return;
        setState({ data: null, loading: false, error, status: null });
      });

    return () => controller.abort();
  }, [url, attempt]);

  const reload = useCallback(() => setAttempt((n) => n + 1), []);
  return { ...state, noData: state.status === 404, reload };
}

export function useIndicators() {
  const { data } = useFetchJson(`${apiUrl}/indicators/`);
  return useMemo(() => data?.indicators || [], [data]);
}

// Значения показателя по всем территориям за год: { values: {id: value}, unit, noData, loading, error }
export function useIndicatorValues(indicatorCode, year, model) {
  const active = indicatorCode && indicatorCode !== POPULATION;
  const url = active ? `${apiUrl}/indicators/${indicatorCode}/?year=${year}&model=${model}` : null;
  const { data, loading, error, noData, reload } = useFetchJson(url);

  const values = useMemo(() => {
    const result = {};
    (data || []).forEach((row) => { result[row.territory_id] = row.value; });
    return result;
  }, [data]);

  return { values, unit: data?.[0]?.unit || '', noData, loading, error, reload };
}

export function usePopulation(territoryId, year, model) {
  const url = territoryId ? `${apiUrl}/population/?territory_id=${territoryId}&year=${year}&model=${model}` : null;
  const { data, loading, error, noData } = useFetchJson(url);
  return { records: data || [], loading, error, noData };
}

// Ряд показателя для района: исторические значения и прогноз выбранной модели
export function useIndicatorSeries(indicatorCode, territoryId, model) {
  const active = indicatorCode && indicatorCode !== POPULATION && territoryId;
  const base = `${apiUrl}/indicators/${indicatorCode}/series/?territory_id=${territoryId}`;
  const history = useFetchJson(active ? `${base}&model=historical` : null);
  const forecast = useFetchJson(active ? `${base}&model=${model}` : null);

  return {
    history: history.data || [],
    forecast: forecast.data || [],
    loading: history.loading || forecast.loading,
  };
}
