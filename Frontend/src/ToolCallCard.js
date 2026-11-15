import { useMemo, useState } from 'react';
import { copyText } from './Markdown';
import { indicatorName } from './indicators';

const ICONS = {
  list_indicators: <path d="M4 5h12M4 10h12M4 15h8" fill="none" stroke="currentColor" strokeWidth="1.8" strokeLinecap="round" />,
  search_territories: <><circle cx="9" cy="9" r="5" fill="none" stroke="currentColor" strokeWidth="1.8" /><path d="M13 13l4 4" stroke="currentColor" strokeWidth="1.8" strokeLinecap="round" /></>,
  get_series: <path d="M3 15l4-5 3 3 6-8" fill="none" stroke="currentColor" strokeWidth="1.8" strokeLinecap="round" strokeLinejoin="round" />,
  rank_territories: <><rect x="3" y="10" width="3.5" height="7" rx="1" fill="currentColor" /><rect x="8.25" y="5" width="3.5" height="12" rx="1" fill="currentColor" /><rect x="13.5" y="8" width="3.5" height="9" rx="1" fill="currentColor" /></>,
  compare_years: <path d="M4 7h11l-3-3M16 13H5l3 3" fill="none" stroke="currentColor" strokeWidth="1.8" strokeLinecap="round" strokeLinejoin="round" />,
  region_totals: <path d="M10 3v7l5 3M10 17a7 7 0 110-14 7 7 0 010 14z" fill="none" stroke="currentColor" strokeWidth="1.8" strokeLinecap="round" strokeLinejoin="round" />,
  territory_profile: <><circle cx="10" cy="7" r="3" fill="none" stroke="currentColor" strokeWidth="1.8" /><path d="M4 17c0-3.3 2.7-5 6-5s6 1.7 6 5" fill="none" stroke="currentColor" strokeWidth="1.8" strokeLinecap="round" /></>,
  run_sql: <path d="M7 6l-4 4 4 4M13 6l4 4-4 4" fill="none" stroke="currentColor" strokeWidth="1.8" strokeLinecap="round" strokeLinejoin="round" />,
};

const COUNT_KEYS = ['rows', 'series', 'results', 'regions', 'indicators', 'values', 'top_growth', 'row_count'];

// id территории -> название: достаём из любых результатов инструментов в диалоге (в том числе обрезанных)
export function collectTerritoryNames(messages) {
  const names = new Map();
  messages.forEach((m) => {
    (m.parts || []).forEach((part) => {
      if (part.type !== 'tool' || !part.preview) return;
      for (const match of part.preview.matchAll(/"id":\s*(\d+),\s*"name_ru":\s*"([^"]+)"/g)) {
        names.set(Number(match[1]), match[2]);
      }
    });
  });
  return names;
}

// Аргументы вызова -> читаемые «чипы»
function describeArguments(name, args, { t, indicators, language, territoryNames }) {
  const chips = [];
  const add = (labelKey, value) => { if (value !== undefined && value !== null && value !== '') chips.push({ label: t(labelKey), value: String(value) }); };
  const territory = (id) => territoryNames.get(Number(id)) || `ID ${id}`;

  if (args.indicator !== undefined) {
    const found = indicators.find((i) => i.code === args.indicator || i.key === args.indicator);
    add('arg.indicator', found ? indicatorName(found, language) : (args.indicator === 'population' ? t('indicator.population') : args.indicator));
  }
  if (args.query !== undefined && name === 'search_territories') add('arg.query', args.query);
  if (args.territory_ids) add('arg.territories', args.territory_ids.map(territory).join(', '));
  if (args.territory_id !== undefined) add('arg.territory', territory(args.territory_id));
  if (args.year !== undefined) add('arg.year', args.year);
  if (args.year_from !== undefined || args.year_to !== undefined) add('arg.years', `${args.year_from ?? '…'}–${args.year_to ?? '…'}`);
  if (args.model && args.model !== 'historical') add('arg.model', args.model);
  if (args.models) add('arg.models', args.models.map((m) => (m === 'historical' ? t('arg.model.historical') : m)).join(', '));
  if (args.top_n !== undefined) add('arg.top', args.top_n);
  if (args.order) add('arg.order', t(`arg.order.${args.order}`));
  if (args.oblast) add('arg.oblast', args.oblast);
  if (args.scope && args.scope !== 'districts') add('arg.scope', t(`arg.scope.${args.scope}`));
  if (args.gender && args.gender !== 'total') add('arg.gender', t(`arg.gender.${args.gender}`));
  if (name === 'run_sql' && args.query) add('arg.sql', args.query.replace(/\s+/g, ' ').slice(0, 70) + (args.query.length > 70 ? '…' : ''));
  return chips;
}

function prettyResult(part) {
  if (!part.preview) return '';
  if (!part.truncated) {
    try { return JSON.stringify(JSON.parse(part.preview), null, 2); } catch (e) { /* не JSON — покажем как есть */ }
  }
  return part.preview;
}

function StatusIcon({ status }) {
  if (status === 'running') return <span className="tool-card__spinner" aria-hidden="true" />;
  const paths = {
    ok: <path d="M4 10.5l4 4 8-9" fill="none" stroke="currentColor" strokeWidth="2.2" strokeLinecap="round" strokeLinejoin="round" />,
    error: <path d="M5 5l10 10M15 5L5 15" fill="none" stroke="currentColor" strokeWidth="2.2" strokeLinecap="round" />,
    cancelled: <path d="M5 10h10" fill="none" stroke="currentColor" strokeWidth="2.2" strokeLinecap="round" />,
  };
  return <svg width="16" height="16" viewBox="0 0 20 20" aria-hidden="true" focusable="false">{paths[status]}</svg>;
}

export default function ToolCallCard({ t, language, part, indicators, territoryNames }) {
  const [open, setOpen] = useState(false);
  const [copied, setCopied] = useState(false);

  const chips = useMemo(
    () => describeArguments(part.name, part.arguments || {}, { t, indicators, language, territoryNames }),
    [part.name, part.arguments, t, indicators, language, territoryNames]
  );
  const countKey = COUNT_KEYS.find((key) => part.counts && part.counts[key] !== undefined);
  const title = t(`tool.${part.name}`);
  const label = title === `tool.${part.name}` ? part.name : title;
  const result = prettyResult(part);

  const onCopy = async () => {
    if (await copyText(result)) {
      setCopied(true);
      setTimeout(() => setCopied(false), 1500);
    }
  };

  return (
    <div className={`tool-card tool-card--${part.status}`}>
      <button type="button" className="tool-card__header" aria-expanded={open} onClick={() => setOpen((v) => !v)}>
        <span className="tool-card__icon" aria-hidden="true">
          <svg width="18" height="18" viewBox="0 0 20 20" focusable="false">{ICONS[part.name] || ICONS.run_sql}</svg>
        </span>
        <span className="tool-card__main">
          <span className="tool-card__title">{label}</span>
          {chips.length > 0 && (
            <span className="tool-card__chips">
              {chips.map((chip) => (
                <span className="chip" key={chip.label + chip.value}><span className="chip__label">{chip.label}</span>{chip.value}</span>
              ))}
            </span>
          )}
        </span>
        <span className="tool-card__status" title={t(`chat.status.${part.status}`)}>
          {countKey && part.status === 'ok' && <span className="tool-card__count">{t(`chat.tool.${countKey === 'row_count' ? 'rows' : countKey}`, { n: part.counts[countKey] })}</span>}
          {part.durationMs !== undefined && <span className="tool-card__time">{part.durationMs < 1000 ? `${part.durationMs} ${language === 'english' ? 'ms' : 'мс'}` : t('chat.meta.seconds', { n: (part.durationMs / 1000).toFixed(1) })}</span>}
          <span className={`tool-card__state tool-card__state--${part.status}`}><StatusIcon status={part.status} /></span>
          <svg className={`tool-card__chevron${open ? ' tool-card__chevron--open' : ''}`} width="14" height="14" viewBox="0 0 16 16" aria-hidden="true" focusable="false">
            <path d="M3.5 6l4.5 4.5L12.5 6" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round" />
          </svg>
        </span>
      </button>

      {open && (
        <div className="tool-card__details">
          <div className="tool-card__section">
            <div className="tool-card__section-title">{t('chat.tool.arguments')}</div>
            <pre className="tool-card__code">{JSON.stringify(part.arguments, null, 2)}</pre>
          </div>
          <div className="tool-card__section">
            <div className="tool-card__section-title">
              {t('chat.tool.result')}
              {result && <button type="button" className="tool-card__copy" onClick={onCopy}>{copied ? t('chat.copied') : t('chat.copy')}</button>}
            </div>
            {result ? <pre className="tool-card__code">{result}</pre> : <p className="tool-card__empty">{t('chat.tool.noResult')}</p>}
            {part.truncated && <p className="tool-card__note">{t('chat.tool.truncated')}</p>}
          </div>
        </div>
      )}
    </div>
  );
}
