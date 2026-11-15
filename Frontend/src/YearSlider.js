import { useEffect, useMemo, useRef, useState } from 'react';
import { MAX_YEAR, MIN_YEAR } from './config';
import './YearSlider.css';

function Icon({ name }) {
  const paths = {
    play: <path d="M6 4.5v11l9-5.5-9-5.5z" fill="currentColor" />,
    pause: <><rect x="5" y="4" width="3.6" height="12" rx="1" fill="currentColor" /><rect x="11.4" y="4" width="3.6" height="12" rx="1" fill="currentColor" /></>,
    prev: <path d="M12.5 4.5L7 10l5.5 5.5" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round" />,
    next: <path d="M7.5 4.5L13 10l-5.5 5.5" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round" />,
  };
  return <svg width="20" height="20" viewBox="0 0 20 20" aria-hidden="true" focusable="false">{paths[name]}</svg>;
}

const PLAY_INTERVAL_MS = 900;

export default function YearSlider({ t, year, onYearChange, lastHistoricalYear, sourceLabel }) {
  const [playing, setPlaying] = useState(false);
  const yearRef = useRef(year);
  yearRef.current = year;

  const years = useMemo(() => Array.from({ length: MAX_YEAR - MIN_YEAR + 1 }, (_, i) => MIN_YEAR + i), []);
  const isForecast = year > lastHistoricalYear;
  const span = MAX_YEAR - MIN_YEAR;

  // доля шкалы (0..1) по году
  const share = (value) => (value - MIN_YEAR) / span;

  useEffect(() => {
    if (!playing) return undefined;
    const timer = setInterval(() => {
      if (yearRef.current >= MAX_YEAR) {
        setPlaying(false);
        return;
      }
      onYearChange(yearRef.current + 1);
    }, PLAY_INTERVAL_MS);
    return () => clearInterval(timer);
  }, [playing, onYearChange]);

  const togglePlay = () => {
    if (!playing && year >= MAX_YEAR) onYearChange(MIN_YEAR);
    setPlaying((value) => !value);
  };

  const step = (delta) => {
    setPlaying(false);
    onYearChange(Math.min(MAX_YEAR, Math.max(MIN_YEAR, year + delta)));
  };

  return (
    <div className="year-slider" style={{ '--share': share(year), '--forecast-start': share(lastHistoricalYear + 0.5) }}>
      <div className="year-slider__controls">
        <button type="button" className="icon-button" onClick={() => step(-1)} disabled={year <= MIN_YEAR}
                aria-label={t('slider.prev')} title={t('slider.prev')}>
          <Icon name="prev" />
        </button>
        <button type="button" className="icon-button icon-button--primary" onClick={togglePlay}
                aria-label={playing ? t('slider.pause') : t('slider.play')}
                title={playing ? t('slider.pause') : t('slider.play')}>
          <Icon name={playing ? 'pause' : 'play'} />
        </button>
        <button type="button" className="icon-button" onClick={() => step(1)} disabled={year >= MAX_YEAR}
                aria-label={t('slider.next')} title={t('slider.next')}>
          <Icon name="next" />
        </button>
      </div>

      <div className="year-slider__current" aria-live="polite">
        <span className="year-slider__year">{year}</span>
        <span className={`source-chip${isForecast ? ' source-chip--forecast' : ''}`} title={sourceLabel}>{sourceLabel}</span>
      </div>

      <div className="year-slider__track-area">
        <div className="year-slider__track" aria-hidden="true">
          <div className="year-slider__forecast-zone" />
          <div className="year-slider__fill" />
        </div>
        <input
          type="range"
          className="year-slider__input"
          min={MIN_YEAR}
          max={MAX_YEAR}
          step={1}
          value={year}
          aria-label={t('slider.label')}
          aria-valuetext={`${year}`}
          onChange={(event) => { setPlaying(false); onYearChange(Number(event.target.value)); }}
        />
        <div className="year-slider__ticks" aria-hidden="true">
          {years.map((value) => {
            const major = value % 5 === 0 || value === MIN_YEAR || value === MAX_YEAR;
            return (
              <button
                key={value}
                type="button"
                tabIndex={-1}
                className={
                  'tick'
                  + (major ? ' tick--major' : '')
                  + (value === year ? ' tick--active' : '')
                  + (value > lastHistoricalYear ? ' tick--forecast' : '')
                }
                style={{ '--tick-share': share(value) }}
                onClick={() => { setPlaying(false); onYearChange(value); }}
              >
                <span className="tick__mark" />
                <span className="tick__label">{value}</span>
              </button>
            );
          })}
        </div>
        <div className="year-slider__zones" aria-hidden="true">
          <span>{t('slider.historyZone')}</span>
          <span style={{ left: 'calc(var(--thumb) / 2 + (100% - var(--thumb)) * var(--forecast-start))' }}>
            {t('slider.forecastZone')}
          </span>
        </div>
      </div>
    </div>
  );
}
