import { Suspense, lazy, useEffect, useMemo, useState } from 'react';
import './App.css';
import Header from './Header';
import BelarusDistrictMap from './Map';
import BelarusDistrictTable from './BelarusDistrictTable';
import YearSlider from './YearSlider';
import { useChat } from './useChat';
import belarusGeoJson from './belarus-districts.json';
import { LANGUAGES, createT } from './i18n';
import { MODELS, POPULATION, lastHistoricalYear } from './config';
import { useIndicators, usePersistentState } from './hooks';

// страница чата подгружается при первом открытии: markdown-библиотеки не нужны карте и таблице
const ChatPage = lazy(() => import('./Chat'));

const TABS = ['map', 'table', 'chat'];

// Сохранённое значение могло устареть (например, после обновления списка моделей)
const pick = (value, allowed, fallback) => (allowed.includes(value) ? value : fallback);

function App() {
  const [storedLanguage, setLanguage] = usePersistentState('demography.language', 'russian');
  const [storedModel, setModel] = usePersistentState('demography.model', 'prophet');
  const [storedIndicator, setIndicator] = usePersistentState('demography.indicator', POPULATION);
  const [storedTab, setTab] = usePersistentState('demography.tab', 'map');
  const [year, setYear] = useState(2024);

  const indicators = useIndicators();
  const language = pick(storedLanguage, LANGUAGES.map((item) => item.value), 'russian');
  const model = pick(storedModel, MODELS, 'prophet');
  const tab = pick(storedTab, TABS, 'map');

  // пока список показателей не загружен, сохранённый выбор принимается как есть
  const indicator = indicators.length === 0 || storedIndicator === POPULATION
    || indicators.some((item) => item.code === storedIndicator)
    ? storedIndicator
    : POPULATION;

  const t = useMemo(() => createT(language), [language]);

  // состояние чата живёт здесь: ответ продолжает приходить, даже если переключиться на другую вкладку
  const chat = useChat({ language, t });

  useEffect(() => {
    document.documentElement.lang = language === 'english' ? 'en' : 'ru';
    document.title = t('app.title');
  }, [language, t]);

  // что показывается в выбранном году: данные Белстата или прогноз модели
  const lastYear = lastHistoricalYear(indicator);
  const isForecast = year > lastYear;
  const source = {
    isForecast,
    label: isForecast ? t('source.forecast') : t('source.historical'),
  };

  return (
    <div className="app">
      <Header
        t={t}
        language={language}
        onLanguageChange={setLanguage}
        model={model}
        onModelChange={setModel}
        tab={tab}
        onTabChange={setTab}
        indicators={indicators}
        indicator={indicator}
        onIndicatorChange={setIndicator}
      />

      <main className="app-main">
        {tab === 'map' && (
          <BelarusDistrictMap
            t={t}
            geoJson={belarusGeoJson}
            year={year}
            model={model}
            language={language}
            indicators={indicators}
            indicator={indicator}
            source={source}
          />
        )}
        {tab === 'table' && (
          <BelarusDistrictTable
            t={t}
            language={language}
            year={year}
            model={model}
            indicators={indicators}
            indicator={indicator}
          />
        )}
        {tab === 'chat' && (
          <Suspense fallback={<div className="page-loading" role="status">{t('common.loading')}</div>}>
            <ChatPage t={t} language={language} indicators={indicators} chat={chat} />
          </Suspense>
        )}
      </main>

      {tab !== 'chat' && (
        <footer className="app-footer">
          <YearSlider t={t} year={year} onYearChange={setYear} lastHistoricalYear={lastYear} sourceLabel={source.label} />
        </footer>
      )}
    </div>
  );
}

export default App;
