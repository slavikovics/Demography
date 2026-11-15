import { useMemo, useState } from 'react';
import { apiUrl, BELARUS_ID, POPULATION } from './config';
import { formatNumber, formatSigned, localeOf, localizeUnit } from './format';
import { useFetchJson } from './hooks';
import { indicatorName, isSigned } from './indicators';
import './BelarusDistrictTable.css';

const SKELETON_ROWS = 8;

// Единый формат строк для населения и показателей
function normalizeRows(data, populationMode) {
  return (data || []).map((row) => ({
    id: row.id,
    name_ru: row.name_ru,
    name_en: row.name_en,
    value: populationMode ? row.people : row.value,
    unit: populationMode ? 'чел.' : row.unit,
  }));
}

const isRepublic = (row) => row.id === BELARUS_ID || row.name_en === 'Republic of Belarus';

function SummaryCard({ label, value, hint, accent }) {
  return (
    <div className={`summary-card${accent ? ' summary-card--accent' : ''}`}>
      <div className="summary-card__label">{label}</div>
      <div className="summary-card__value">{value}</div>
      {hint && <div className="summary-card__hint">{hint}</div>}
    </div>
  );
}

function SortIndicator({ state }) {
  return (
    <svg className={`sort-icon sort-icon--${state}`} width="10" height="14" viewBox="0 0 10 14" aria-hidden="true" focusable="false">
      <path d="M5 1L9 5.5H1z" className="sort-icon__up" />
      <path d="M5 13L1 8.5h8z" className="sort-icon__down" />
    </svg>
  );
}

function downloadCsv(rows, columns, fileName) {
  const escape = (cell) => `"${String(cell ?? '').replace(/"/g, '""')}"`;
  const lines = [columns.map((c) => escape(c.title)).join(',')];
  rows.forEach((row) => lines.push(columns.map((c) => escape(c.get(row))).join(',')));

  const blob = new Blob([`﻿${lines.join('\n')}`], { type: 'text/csv;charset=utf-8' });
  const url = URL.createObjectURL(blob);
  const link = document.createElement('a');
  link.href = url;
  link.download = fileName;
  document.body.appendChild(link);
  link.click();
  link.remove();
  URL.revokeObjectURL(url);
}

function BelarusDistrictTable({ t, language, year, model, indicators, indicator }) {
  const populationMode = indicator === POPULATION;
  const indicatorMeta = indicators.find((item) => item.code === indicator);
  const signed = isSigned(indicator);
  const format = signed ? formatSigned : formatNumber;
  const nameKey = language === 'english' ? 'name_en' : 'name_ru';

  const [search, setSearch] = useState('');
  const [sort, setSort] = useState({ key: 'value', direction: 'desc' });

  const tableUrl = populationMode
    ? `${apiUrl}/population_table/?year=${year}&model=${model}&sort_by=id&sorting_direction=asc`
    : `${apiUrl}/indicators/${indicator}/table/?year=${year}&model=${model}&sort_by=id&sorting_direction=asc`;
  const table = useFetchJson(tableUrl);
  const interesting = useFetchJson(
    populationMode ? `${apiUrl}/population_table/interesting_data/?year=${year}&model=${model}` : null
  );

  const allRows = useMemo(() => normalizeRows(table.data, populationMode), [table.data, populationMode]);
  const republic = useMemo(() => allRows.find(isRepublic), [allRows]);
  const rows = useMemo(() => allRows.filter((row) => !isRepublic(row)), [allRows]);

  // место в рейтинге не зависит от выбранной сортировки
  const rankById = useMemo(() => {
    const ranked = [...rows].sort((a, b) => b.value - a.value);
    return new Map(ranked.map((row, i) => [row.id, i + 1]));
  }, [rows]);

  const maxAbs = useMemo(() => Math.max(1, ...rows.map((row) => Math.abs(row.value))), [rows]);

  const visibleRows = useMemo(() => {
    const query = search.trim().toLowerCase();
    const filtered = query
      ? rows.filter((row) => `${row.name_ru} ${row.name_en}`.toLowerCase().includes(query))
      : rows;

    const factor = sort.direction === 'asc' ? 1 : -1;
    const collator = new Intl.Collator(localeOf(language));
    return [...filtered].sort((a, b) => {
      if (sort.key === 'name') return factor * collator.compare(a[nameKey] || '', b[nameKey] || '');
      if (sort.key === 'id') return factor * (a.id - b.id);
      return factor * (a.value - b.value);
    });
  }, [rows, search, sort, language, nameKey]);

  const unit = localizeUnit(rows[0]?.unit, language);
  const title = populationMode ? t('table.population') : indicatorName(indicatorMeta, language);
  const valueColumnTitle = t('table.value');

  const toggleSort = (key) => {
    setSort((current) => (
      current.key === key
        ? { key, direction: current.direction === 'asc' ? 'desc' : 'asc' }
        : { key, direction: key === 'name' || key === 'id' ? 'asc' : 'desc' }
    ));
  };

  const columns = [
    { key: 'rank', title: t('table.rank'), sortable: false, className: 'col-rank' },
    { key: 'name', title: t('table.name'), sortable: true, className: 'col-name' },
    { key: 'value', title: valueColumnTitle, sortable: true, className: 'col-value' },
    { key: 'id', title: t('table.id'), sortable: true, className: 'col-id' },
  ];

  const exportCsv = () => downloadCsv(
    visibleRows,
    [
      { title: t('table.id'), get: (row) => row.id },
      { title: t('table.name'), get: (row) => row[nameKey] },
      { title: `${title}${unit ? `, ${unit}` : ''}`, get: (row) => row.value },
    ],
    `${title}_${year}.csv`.replace(/[\\/:*?"<>|\s]+/g, '_')
  );

  // ---------- сводка ----------
  const summary = (() => {
    if (populationMode) {
      const labels = [t('table.minPopulation'), t('table.maxPopulation'), t('table.lowGrowth'), t('table.highGrowth')];
      const cards = [];
      if (republic) {
        cards.push(<SummaryCard key="republic" accent label={t('table.republic')} value={formatNumber(republic.value, language, 0)} />);
      }
      (interesting.data?.fields || []).forEach((entry, i) => {
        const record = entry?.[0];
        if (!record) return;
        const growth = i >= 2;
        cards.push(
          <SummaryCard key={labels[i]} label={labels[i]}
                       value={growth ? formatSigned(record[2], language, 0) : formatNumber(record[2], language, 0)}
                       hint={language === 'english' ? record[1] : record[0]} />
        );
      });
      return cards;
    }

    if (rows.length === 0) return [];
    const best = rows.reduce((a, b) => (b.value > a.value ? b : a));
    const worst = rows.reduce((a, b) => (b.value < a.value ? b : a));
    const average = rows.reduce((sum, row) => sum + row.value, 0) / rows.length;
    return [
      republic && <SummaryCard key="republic" accent label={t('table.republic')} value={format(republic.value, language)} hint={unit} />,
      <SummaryCard key="max" label={t('table.max')} value={format(best.value, language)} hint={best[nameKey]} />,
      <SummaryCard key="min" label={t('table.min')} value={format(worst.value, language)} hint={worst[nameKey]} />,
      <SummaryCard key="avg" label={t('table.average')} value={format(average, language)} hint={unit} />,
      <SummaryCard key="count" label={t('table.count')} value={formatNumber(rows.length, language, 0)} />,
    ].filter(Boolean);
  })();

  const loading = table.loading && !table.data;
  const empty = !loading && !table.error && (table.noData || rows.length === 0);

  return (
    <div className="table-page">
      <aside className="table-sidebar" aria-label={t('table.summary')}>
        <h2 className="table-sidebar__title">{t('table.summary')}</h2>
        <div className="table-sidebar__cards">
          {loading
            ? Array.from({ length: 4 }, (_, i) => <div key={i} className="skeleton skeleton--card" />)
            : summary}
        </div>
      </aside>

      <section className="table-card" aria-label={title}>
        <div className="table-toolbar">
          <div className="table-toolbar__heading">
            <h2 className="table-toolbar__title">{title}</h2>
            <p className="table-toolbar__subtitle">
              {year}{unit ? ` · ${unit}` : ''}
              {!table.loading && rows.length > 0 && ` · ${t('table.shown', { shown: visibleRows.length, total: rows.length })}`}
            </p>
          </div>

          <div className="table-toolbar__actions">
            <div className="search">
              <svg className="search__icon" width="16" height="16" viewBox="0 0 16 16" aria-hidden="true" focusable="false">
                <circle cx="7" cy="7" r="4.5" fill="none" stroke="currentColor" strokeWidth="1.8" />
                <path d="M10.5 10.5L14 14" stroke="currentColor" strokeWidth="1.8" strokeLinecap="round" />
              </svg>
              <input
                type="search"
                className="search__input"
                value={search}
                placeholder={t('table.search')}
                aria-label={t('table.search')}
                onChange={(event) => setSearch(event.target.value)}
              />
              {search && (
                <button type="button" className="search__clear" onClick={() => setSearch('')} aria-label={t('table.clearSearch')}>
                  <svg width="12" height="12" viewBox="0 0 12 12" aria-hidden="true" focusable="false">
                    <path d="M2.5 2.5l7 7M9.5 2.5l-7 7" stroke="currentColor" strokeWidth="1.8" strokeLinecap="round" />
                  </svg>
                </button>
              )}
            </div>
            <button type="button" className="button-secondary" onClick={exportCsv} disabled={visibleRows.length === 0}>
              <svg width="14" height="14" viewBox="0 0 14 14" aria-hidden="true" focusable="false">
                <path d="M7 1.5v7M4 6l3 3 3-3M2 11.5h10" fill="none" stroke="currentColor" strokeWidth="1.6"
                      strokeLinecap="round" strokeLinejoin="round" />
              </svg>
              {t('table.export')}
            </button>
          </div>
        </div>

        <div className="table-scroll">
          {table.error ? (
            <div className="state-message state-message--error" role="alert">
              <strong>{t('common.error')}</strong>
              <span>{t('common.errorHint')}</span>
              <button type="button" className="button-secondary" onClick={table.reload}>{t('common.retry')}</button>
            </div>
          ) : empty ? (
            <div className="state-message">
              <strong>{t('table.noData')}</strong>
              <span>{t('table.noDataHint')}</span>
            </div>
          ) : (
            <table className="data-table">
              <thead>
                <tr>
                  {columns.map((column) => {
                    const state = sort.key === column.key ? sort.direction : 'none';
                    return (
                      <th key={column.key} className={column.className} scope="col"
                          aria-sort={state === 'asc' ? 'ascending' : state === 'desc' ? 'descending' : undefined}>
                        {column.sortable ? (
                          <button type="button" className="th-button" onClick={() => toggleSort(column.key)}
                                  title={t('table.sortBy', { column: column.title })}>
                            {column.title}
                            <SortIndicator state={state} />
                          </button>
                        ) : column.title}
                      </th>
                    );
                  })}
                </tr>
              </thead>
              <tbody>
                {loading ? (
                  Array.from({ length: SKELETON_ROWS }, (_, i) => (
                    <tr key={i} aria-hidden="true">
                      <td colSpan={columns.length}><div className="skeleton skeleton--row" /></td>
                    </tr>
                  ))
                ) : visibleRows.length === 0 ? (
                  <tr>
                    <td colSpan={columns.length}>
                      <div className="state-message">
                        <strong>{t('table.noResults')}</strong>
                        <span>{t('table.noResultsHint')}</span>
                      </div>
                    </td>
                  </tr>
                ) : (
                  visibleRows.map((row) => {
                    const share = (Math.abs(row.value) / maxAbs) * (signed ? 50 : 100);
                    const negative = row.value < 0;
                    return (
                      <tr key={row.id}>
                        <td className="col-rank">{rankById.get(row.id)}</td>
                        <td className="col-name">{row[nameKey] || row.name_ru}</td>
                        <td className="col-value">
                          <div className="value-cell">
                            <span className="value-number">{format(row.value, language, populationMode ? 0 : 1)}</span>
                            <span className={`value-track${signed ? ' value-track--signed' : ''}`} aria-hidden="true">
                              <span
                                className={`value-bar${negative ? ' value-bar--negative' : ''}`}
                                style={signed
                                  ? { left: negative ? `${50 - share}%` : '50%', width: `${share}%` }
                                  : { left: 0, width: `${share}%` }}
                              />
                            </span>
                          </div>
                        </td>
                        <td className="col-id">{row.id}</td>
                      </tr>
                    );
                  })
                )}
              </tbody>
            </table>
          )}
        </div>
      </section>
    </div>
  );
}

export default BelarusDistrictTable;
