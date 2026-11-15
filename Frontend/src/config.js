export const apiUrl = process.env.REACT_APP_API_URL || 'http://localhost:5000';

// Режим «Население» — исходный режим приложения, без дополнительного показателя
export const POPULATION = 'population';

export const MIN_YEAR = 2010;
export const MAX_YEAR = 2034;

// Последний год с опубликованными данными: дальше значения — прогноз выбранной модели
export const LAST_HISTORICAL_POPULATION_YEAR = 2024;
export const LAST_HISTORICAL_INDICATOR_YEAR = 2025;

export const BELARUS_ID = 699961;
export const MINSK_ID = 919071;

export const MODELS = ['prophet', 'linear', 'exponential'];

export const lastHistoricalYear = (indicatorCode) =>
  indicatorCode === POPULATION ? LAST_HISTORICAL_POPULATION_YEAR : LAST_HISTORICAL_INDICATOR_YEAR;
