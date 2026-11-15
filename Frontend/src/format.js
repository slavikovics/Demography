const LOCALES = { russian: 'ru-RU', english: 'en-US' };

export const localeOf = (language) => LOCALES[language] || LOCALES.russian;

export function formatNumber(value, language = 'russian', maxFractionDigits = 1) {
  if (value === null || value === undefined || Number.isNaN(Number(value))) return '—';
  return Number(value).toLocaleString(localeOf(language), { maximumFractionDigits: maxFractionDigits });
}

// Знак для прироста/убыли: +1 234 / −1 234
export function formatSigned(value, language = 'russian', maxFractionDigits = 1) {
  if (value === null || value === undefined || Number.isNaN(Number(value))) return '—';
  const text = formatNumber(Math.abs(value), language, maxFractionDigits);
  if (value > 0) return `+${text}`;
  if (value < 0) return `−${text}`;
  return text;
}

export function formatPercent(fraction, language = 'russian') {
  if (fraction === null || fraction === undefined || Number.isNaN(fraction)) return '—';
  return `${formatNumber(fraction * 100, language, 1)}%`;
}

// Единицы измерения приходят с API на русском — локализуем их на клиенте
const UNITS = {
  'чел.': { russian: 'чел.', english: 'people' },
  'промилле': { russian: 'на 1000 чел.', english: 'per 1,000 people' },
  'Человек на квадратный километр': { russian: 'чел. на км²', english: 'people per km²' },
  'единиц': { russian: 'ед.', english: 'units' },
  'тыс. чел.': { russian: 'тыс. чел.', english: 'thousand people' },
  'процентов': { russian: '%', english: '%' },
  'коэффициент': { russian: 'коэффициент', english: 'coefficient' },
};

export function localizeUnit(unit, language = 'russian') {
  if (!unit) return '';
  return UNITS[unit]?.[language] || unit;
}
