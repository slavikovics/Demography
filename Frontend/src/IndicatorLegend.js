import { useState } from 'react';
import { formatNumber, formatSigned, localizeUnit } from './format';

// Легенда карты: интервалы квантильной шкалы, единица измерения и цвет «нет значения».
// На узких экранах по умолчанию свёрнута, чтобы не закрывать карту.
export default function IndicatorLegend({ t, language, name, unit, buckets, noData, year, signed }) {
  const [collapsed, setCollapsed] = useState(() => window.innerWidth < 720);
  const format = signed ? formatSigned : formatNumber;

  return (
    <section className="legend" aria-label={t('legend.title')}>
      <button type="button" className="legend__toggle" onClick={() => setCollapsed((value) => !value)}
              aria-expanded={!collapsed}
              aria-label={`${t('legend.title')}: ${collapsed ? t('common.expand') : t('common.collapse')}`}>
        <span className="legend__heading">
          <span className="legend__title">{name}</span>
          {unit && <span className="legend__unit">{localizeUnit(unit, language)}</span>}
        </span>
        <svg className="legend__chevron" width="16" height="16" viewBox="0 0 16 16" aria-hidden="true" focusable="false"
             style={{ transform: collapsed ? 'none' : 'rotate(180deg)' }}>
          <path d="M3.5 6l4.5 4.5L12.5 6" fill="none" stroke="currentColor" strokeWidth="2"
                strokeLinecap="round" strokeLinejoin="round" />
        </svg>
      </button>

      {!collapsed && (noData ? (
        <div className="legend__empty">
          <strong>{t('legend.noData', { year })}</strong>
          <span>{t('legend.noDataHint')}</span>
        </div>
      ) : (
        <ul className="legend__list">
          {buckets.map((bucket) => (
            <li key={bucket.color + bucket.from} className="legend__row">
              <span className="legend__swatch" style={{ background: bucket.color }} />
              <span>{format(bucket.from, language)} – {format(bucket.to, language)}</span>
            </li>
          ))}
          <li className="legend__row legend__row--muted">
            <span className="legend__swatch legend__swatch--empty" />
            <span>{t('common.noValue')}</span>
          </li>
        </ul>
      ))}
    </section>
  );
}
