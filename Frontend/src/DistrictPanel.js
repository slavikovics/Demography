import TerritoryStats from './TerritoryStats';

function Badge({ source }) {
  return <span className={`badge${source.isForecast ? ' badge--forecast' : ''}`}>{source.label}</span>;
}

// Боковая панель выбранного района (заменяет popup, который перекрывал карту)
export default function DistrictPanel({
  t, language, feature, year, model, indicatorInfo, regionIds, source, onClose,
}) {
  if (!feature) return null;
  const { shapeName, shapeNameRu, regionId } = feature.properties;
  const title = language === 'russian' && shapeNameRu ? shapeNameRu : shapeName;

  return (
    <aside className="side-panel" aria-label={title}>
      <header className="card-header">
        <div className="card-header__main">
          <h2 className="card-header__title">{title}</h2>
          <div className="card-header__meta">
            <span>{t('common.year')}: <strong>{year}</strong></span>
            <span>{t('common.regionId')}: <strong>{regionId}</strong></span>
          </div>
          <Badge source={source} />
        </div>
        <button type="button" className="card-header__close" onClick={onClose}
                aria-label={t('common.close')} title={t('common.close')}>
          <svg width="16" height="16" viewBox="0 0 16 16" aria-hidden="true" focusable="false">
            <path d="M3.5 3.5l9 9M12.5 3.5l-9 9" stroke="currentColor" strokeWidth="2" strokeLinecap="round" />
          </svg>
        </button>
      </header>

      <div className="card-body">
        <TerritoryStats t={t} language={language} territoryId={regionId} year={year} model={model}
                        indicatorInfo={indicatorInfo} regionIds={regionIds} showTrend />
      </div>
    </aside>
  );
}
