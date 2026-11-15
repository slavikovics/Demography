import { useMemo } from 'react';
import { BELARUS_ID } from './config';
import { formatNumber, formatPercent, formatSigned, localizeUnit } from './format';
import { computeRank } from './indicators';
import { useIndicatorSeries, usePopulation } from './hooks';
import Sparkline from './Sparkline';

const sumBy = (records, names) =>
  records.filter((r) => names.includes(String(r.gender).toLowerCase())).reduce((sum, r) => sum + r.people, 0);

function PopulationBlock({ t, language, records, loading, error, noData }) {
  const totals = useMemo(() => {
    const male = sumBy(records, ['males', 'male']);
    const female = sumBy(records, ['females', 'female']);
    const total = sumBy(records, ['total', 'total population']) || male + female;
    return { male, female, total };
  }, [records]);

  if (loading) {
    return (
      <div className="skeleton-group" aria-busy="true" aria-label={t('common.loading')}>
        <div className="skeleton skeleton--title" />
        <div className="skeleton-row"><div className="skeleton" /><div className="skeleton" /></div>
      </div>
    );
  }

  if (error || noData || records.length === 0) {
    return (
      <div className="empty-note">
        <strong>{error ? t('common.error') : t('panel.noData')}</strong>
      </div>
    );
  }

  const malePart = totals.total ? totals.male / totals.total : 0;
  const femalePart = totals.total ? totals.female / totals.total : 0;

  return (
    <section className="population-block" aria-label={t('panel.population')}>
      <div className="population-block__total">
        <span className="population-block__label">{t('panel.population')}</span>
        <span className="population-block__number">{formatNumber(totals.total, language, 0)}</span>
      </div>

      <div className="split" role="img"
           aria-label={`${t('panel.male')} ${formatPercent(malePart, language)}, ${t('panel.female')} ${formatPercent(femalePart, language)}`}>
        <div className="split__male" style={{ width: `${malePart * 100}%` }} />
        <div className="split__female" style={{ width: `${femalePart * 100}%` }} />
      </div>

      <div className="population-block__genders">
        <div className="gender gender--male">
          <span className="gender__label">{t('panel.male')}</span>
          <span className="gender__value">{formatNumber(totals.male, language, 0)}</span>
          <span className="gender__share">{formatPercent(malePart, language)}</span>
        </div>
        <div className="gender gender--female">
          <span className="gender__label">{t('panel.female')}</span>
          <span className="gender__value">{formatNumber(totals.female, language, 0)}</span>
          <span className="gender__share">{formatPercent(femalePart, language)}</span>
        </div>
      </div>
    </section>
  );
}

function IndicatorBlock({ t, language, info, territoryId, regionIds, showTrend, year, model }) {
  const value = info.values[territoryId];
  const republic = info.values[BELARUS_ID];
  const rank = regionIds && territoryId !== BELARUS_ID ? computeRank(info.values, territoryId, regionIds) : null;
  const series = useIndicatorSeries(showTrend ? info.code : null, territoryId, model);
  const missing = info.noData || value === undefined;
  const format = info.signed ? formatSigned : formatNumber;
  const tone = info.signed && !missing ? (value > 0 ? 'positive' : value < 0 ? 'negative' : '') : '';

  return (
    <section className="indicator-card" aria-label={info.name}>
      <div className="indicator-card__name">{info.name}</div>
      <div className={`indicator-card__value ${tone ? `indicator-card__value--${tone}` : ''}`}>
        {missing ? '—' : format(value, language)}
        {!missing && info.unit && <span className="indicator-card__unit">{localizeUnit(info.unit, language)}</span>}
      </div>

      {!missing && (rank || (republic !== undefined && territoryId !== BELARUS_ID)) && (
        <dl className="indicator-card__facts">
          {rank && (
            <div>
              <dt>{t('panel.rank')}</dt>
              <dd>{t('panel.rankValue', { rank: rank.rank, total: rank.total })}</dd>
            </div>
          )}
          {republic !== undefined && territoryId !== BELARUS_ID && (
            <div>
              <dt>{t('panel.vsRepublic')}</dt>
              <dd>{format(republic, language)}</dd>
            </div>
          )}
        </dl>
      )}

      {showTrend && (
        <div className="indicator-card__trend">
          <div className="section-label">{t('panel.trend')}</div>
          {series.loading ? (
            <div className="skeleton skeleton--chart" aria-busy="true" />
          ) : (
            <Sparkline t={t} language={language} history={series.history} forecast={series.forecast}
                       year={year} signed={info.signed} />
          )}
        </div>
      )}
    </section>
  );
}

/**
 * Содержимое карточки территории: значение выбранного показателя (если есть),
 * динамика и население с разбивкой по полу.
 */
export default function TerritoryStats({
  t, language, territoryId, year, model, indicatorInfo, regionIds, showTrend = false,
}) {
  const population = usePopulation(territoryId, year, model);

  return (
    <div className="territory-stats">
      {indicatorInfo && (
        <IndicatorBlock t={t} language={language} info={indicatorInfo} territoryId={territoryId}
                        regionIds={regionIds} showTrend={showTrend} year={year} model={model} />
      )}
      <PopulationBlock t={t} language={language} {...population} />
    </div>
  );
}
