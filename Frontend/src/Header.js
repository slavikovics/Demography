import { useMemo } from 'react';
import Select from './Select';
import { LANGUAGES } from './i18n';
import { MODELS } from './config';
import { buildIndicatorOptions } from './indicators';
import './Header.css';

function BrandMark() {
  return (
    <svg className="brand__mark" width="34" height="34" viewBox="0 0 34 34" aria-hidden="true" focusable="false">
      <defs>
        <linearGradient id="brand-gradient" x1="0" y1="0" x2="1" y2="1">
          <stop offset="0" stopColor="#4299e1" />
          <stop offset="1" stopColor="#38b2ac" />
        </linearGradient>
      </defs>
      <rect width="34" height="34" rx="9" fill="url(#brand-gradient)" />
      <rect x="7" y="17" width="4.5" height="10" rx="1.4" fill="#fff" opacity="0.9" />
      <rect x="14.75" y="11" width="4.5" height="16" rx="1.4" fill="#fff" />
      <rect x="22.5" y="6" width="4.5" height="21" rx="1.4" fill="#fff" opacity="0.9" />
    </svg>
  );
}

function ExternalIcon() {
  return (
    <svg width="12" height="12" viewBox="0 0 12 12" aria-hidden="true" focusable="false">
      <path d="M4.5 2.5h5v5M9.5 2.5l-6.5 6.5" fill="none" stroke="currentColor" strokeWidth="1.5"
            strokeLinecap="round" strokeLinejoin="round" />
    </svg>
  );
}

export default function Header({
  t, language, onLanguageChange, model, onModelChange, tab, onTabChange,
  indicators, indicator, onIndicatorChange,
}) {
  const indicatorOptions = useMemo(
    () => buildIndicatorOptions(indicators, language, t),
    [indicators, language, t]
  );

  const modelOptions = MODELS.map((value) => ({ value, label: t(`model.${value}`) }));
  const languageOptions = LANGUAGES.map(({ value, label }) => ({ value, label }));

  const tabs = [
    { value: 'map', label: t('nav.map') },
    { value: 'table', label: t('nav.table') },
  ];


  return (
    <header className="app-header">
      <div className="brand">
        <BrandMark />
        <div className="brand__text">
          <h1 className="brand__title">{t('app.title')}</h1>
          <p className="brand__subtitle">{t('app.subtitle')}</p>
        </div>
      </div>

      <div className="header-controls">
        <Select
          className="header-controls__indicator"
          label={t('controls.indicator')}
          value={indicator}
          options={indicatorOptions}
          onChange={onIndicatorChange}
        />
        <Select
          className="header-controls__model"
          label={t('controls.model')}
          value={model}
          options={modelOptions}
          onChange={onModelChange}
        />
        <Select
          className="header-controls__language"
          label={t('controls.language')}
          value={language}
          options={languageOptions}
          onChange={onLanguageChange}
          menuAlign="right"
        />
      </div>

      <nav className="header-nav" aria-label={t('nav.views')}>
        <div className="segmented" role="tablist" aria-label={t('nav.views')}>
          {tabs.map((item) => (
            <button
              key={item.value}
              type="button"
              role="tab"
              aria-selected={tab === item.value}
              className={`segmented__item${tab === item.value ? ' segmented__item--active' : ''}`}
              onClick={() => onTabChange(item.value)}
            >
              {item.label}
            </button>
          ))}
        </div>

        <div className="header-links">
          <a className="header-link" href="https://github.com/slavikovics/Demography" target="_blank" rel="noopener noreferrer">
            {t('links.github')} <ExternalIcon />
          </a>
          <a className="header-link" href="https://dataportal.belstat.gov.by/osids/home-page" target="_blank" rel="noopener noreferrer">
            {t('links.belstat')} <ExternalIcon />
          </a>
        </div>
      </nav>
    </header>
  );
}
