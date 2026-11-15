import { useState } from 'react';
import { BELARUS_ID } from './config';
import TerritoryStats from './TerritoryStats';

// Сводка по республике в целом; на узких экранах по умолчанию свёрнута
export default function CountryCard({ t, language, year, model, indicatorInfo, source }) {
  const [collapsed, setCollapsed] = useState(() => window.innerWidth < 720);

  return (
    <section className="country-card" aria-label={t('common.republic')}>
      <header className="card-header card-header--compact">
        <div className="card-header__main">
          <h2 className="card-header__title">{t('common.republic')}</h2>
          <div className="card-header__meta">
            <span>{t('common.year')}: <strong>{year}</strong></span>
            <span className={`badge badge--inline${source.isForecast ? ' badge--forecast' : ''}`}>{source.label}</span>
          </div>
        </div>
        <button type="button" className="card-header__close card-header__toggle" onClick={() => setCollapsed((v) => !v)}
                aria-expanded={!collapsed} aria-label={collapsed ? t('common.expand') : t('common.collapse')}
                title={collapsed ? t('common.expand') : t('common.collapse')}>
          <svg width="16" height="16" viewBox="0 0 16 16" aria-hidden="true" focusable="false"
               style={{ transform: collapsed ? 'none' : 'rotate(180deg)', transition: 'transform 0.2s ease' }}>
            <path d="M3.5 6l4.5 4.5L12.5 6" fill="none" stroke="currentColor" strokeWidth="2"
                  strokeLinecap="round" strokeLinejoin="round" />
          </svg>
        </button>
      </header>

      {!collapsed && (
        <div className="card-body">
          <TerritoryStats t={t} language={language} territoryId={BELARUS_ID} year={year} model={model}
                          indicatorInfo={indicatorInfo} />
        </div>
      )}
    </section>
  );
}
