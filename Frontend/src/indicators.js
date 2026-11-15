import { scaleQuantile, schemeYlOrRd, schemeRdYlBu } from 'd3';
import { BELARUS_ID, MINSK_ID, POPULATION } from './config';

// Показатели, которые бывают отрицательными (прирост/убыль)
const SIGNED_CODES = new Set(['10101200008', '10101200009', '10101300003']);
export const isSigned = (code) => SIGNED_CODES.has(code);

const MARRIAGE_CODES = new Set(['10101200014', '10101200015', '10101200016', '10101200017']);

export function indicatorGroup(code) {
  if (MARRIAGE_CODES.has(code)) return 'marriage';
  if (code.startsWith('101012')) return 'natural';
  if (code.startsWith('101013')) return 'migration';
  return 'population';
}

const GROUP_ORDER = ['population', 'natural', 'marriage', 'migration'];

export function indicatorName(indicator, language) {
  if (!indicator) return '';
  return language === 'english' ? indicator.name_en : indicator.name_ru;
}

// Опции выпадающего списка: «Население» + показатели, сгруппированные по темам
export function buildIndicatorOptions(indicators, language, t) {
  const sorted = [...indicators].sort((a, b) => {
    const byGroup = GROUP_ORDER.indexOf(indicatorGroup(a.code)) - GROUP_ORDER.indexOf(indicatorGroup(b.code));
    return byGroup !== 0 ? byGroup : a.code.localeCompare(b.code);
  });

  return [
    { value: POPULATION, label: t('indicator.population'), group: t('group.population') },
    ...sorted.map((indicator) => ({
      value: indicator.code,
      label: indicatorName(indicator, language),
      group: t(`group.${indicatorGroup(indicator.code)}`),
    })),
  ];
}

// Районы для расчёта шкалы и места: без республики в целом и Минска (иначе они «съедают» палитру)
const isDistrictId = (id) => Number(id) !== BELARUS_ID && Number(id) !== MINSK_ID;

// Квантильная шкала: устойчива к выбросам. Возвращает { colorOf, buckets }
export function buildColorScale(values, signed, regionIds) {
  const idSet = regionIds ? new Set(regionIds.map(Number)) : null;
  const sample = Object.entries(values)
    .filter(([id]) => isDistrictId(id) && (!idSet || idSet.has(Number(id))))
    .map(([, value]) => value);

  if (sample.length === 0) return { colorOf: () => null, buckets: [] };

  const palette = signed ? schemeRdYlBu[7] : schemeYlOrRd[7];
  const scale = scaleQuantile().domain(sample).range(palette);
  const edges = [Math.min(...sample), ...scale.quantiles(), Math.max(...sample)];

  return {
    colorOf: (value) => (value === undefined || value === null ? null : scale(value)),
    buckets: palette.map((color, i) => ({ color, from: edges[i], to: edges[i + 1] })),
  };
}

// Место района среди остальных районов карты (1 — наибольшее значение)
export function computeRank(values, regionId, regionIds) {
  const idSet = new Set(regionIds.map(Number));
  const own = values[regionId];
  if (own === undefined) return null;

  const others = Object.entries(values).filter(([id]) => idSet.has(Number(id)) && isDistrictId(id));
  return { rank: others.filter(([, value]) => value > own).length + 1, total: others.length };
}
