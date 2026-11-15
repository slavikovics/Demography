import { useMemo, useRef, useState } from 'react';
import { extent, line, scaleLinear } from 'd3';
import { MAX_YEAR, MIN_YEAR } from './config';
import { formatNumber, formatSigned } from './format';

const WIDTH = 320;
const HEIGHT = 128;
const MARGIN = { top: 12, right: 12, bottom: 24, left: 46 };

// Разрывы в рядах (например, 2020–2023) не соединяются линией
function toSegments(points) {
  const segments = [];
  let current = [];
  points.forEach((point, i) => {
    if (i > 0 && point.year - points[i - 1].year > 1) {
      segments.push(current);
      current = [];
    }
    current.push(point);
  });
  if (current.length) segments.push(current);
  return segments;
}

/** Динамика показателя: сплошная линия — данные Белстата, пунктир — прогноз. */
export default function Sparkline({ t, language, history, forecast, year, signed }) {
  const svgRef = useRef(null);
  const [hover, setHover] = useState(null);

  const chart = useMemo(() => {
    const historyPoints = history.map((row) => ({ year: row.year, value: row.value }));
    const forecastPoints = forecast.map((row) => ({ year: row.year, value: row.value }));
    const all = [...historyPoints, ...forecastPoints].sort((a, b) => a.year - b.year);
    if (all.length < 2) return null;

    const x = scaleLinear().domain([MIN_YEAR, MAX_YEAR]).range([MARGIN.left, WIDTH - MARGIN.right]);
    let [low, high] = extent(all, (p) => p.value);
    if (signed) { low = Math.min(low, 0); high = Math.max(high, 0); }
    const pad = (high - low) * 0.1 || Math.abs(high) * 0.1 || 1;
    const y = scaleLinear().domain([low - pad, high + pad]).range([HEIGHT - MARGIN.bottom, MARGIN.top]).nice(3);

    const path = line().x((p) => x(p.year)).y((p) => y(p.value));
    const lastHistory = historyPoints[historyPoints.length - 1];
    const forecastLine = forecastPoints.length
      ? path(lastHistory ? [lastHistory, ...forecastPoints] : forecastPoints)
      : null;

    return {
      x, y, all,
      historyPaths: toSegments(historyPoints).filter((s) => s.length > 1).map((s) => path(s)),
      historyDots: toSegments(historyPoints).filter((s) => s.length === 1).map((s) => s[0]),
      forecastLine,
      yTicks: y.ticks(3),
      xTicks: [MIN_YEAR, 2020, MAX_YEAR],
    };
  }, [history, forecast, signed]);

  if (!chart) return <p className="trend__empty">{t('panel.trendEmpty')}</p>;

  const current = chart.all.find((p) => p.year === year);
  const shown = hover ?? current;
  const format = signed ? formatSigned : formatNumber;

  const onMove = (event) => {
    const rect = svgRef.current.getBoundingClientRect();
    const px = ((event.clientX - rect.left) / rect.width) * WIDTH;
    const nearest = chart.all.reduce((best, p) => (
      Math.abs(chart.x(p.year) - px) < Math.abs(chart.x(best.year) - px) ? p : best
    ));
    setHover(nearest);
  };

  return (
    <div className="trend">
      <div className="trend__readout" aria-live="polite">
        {shown ? (
          <>
            <span className="trend__year">{shown.year}</span>
            <span className="trend__value">{format(shown.value, language)}</span>
          </>
        ) : (
          <span className="trend__year">{year}</span>
        )}
      </div>

      <svg ref={svgRef} className="trend__svg" viewBox={`0 0 ${WIDTH} ${HEIGHT}`} role="img"
           aria-label={t('panel.trend')} onMouseMove={onMove} onMouseLeave={() => setHover(null)}>
        {chart.yTicks.map((tick) => (
          <g key={tick}>
            <line x1={MARGIN.left} x2={WIDTH - MARGIN.right} y1={chart.y(tick)} y2={chart.y(tick)}
                  className={tick === 0 ? 'trend__zero' : 'trend__grid'} />
            <text x={MARGIN.left - 8} y={chart.y(tick)} className="trend__axis" textAnchor="end" dominantBaseline="middle">
              {formatNumber(tick, language, 1)}
            </text>
          </g>
        ))}
        {chart.xTicks.map((tick) => (
          <text key={tick} x={chart.x(tick)} y={HEIGHT - 6} className="trend__axis"
                textAnchor={tick === MIN_YEAR ? 'start' : tick === MAX_YEAR ? 'end' : 'middle'}>
            {tick}
          </text>
        ))}

        <line x1={chart.x(year)} x2={chart.x(year)} y1={MARGIN.top} y2={HEIGHT - MARGIN.bottom} className="trend__marker" />
        {chart.historyPaths.map((d, i) => <path key={i} d={d} className="trend__line" />)}
        {chart.historyDots.map((p) => <circle key={p.year} cx={chart.x(p.year)} cy={chart.y(p.value)} r="2.5" className="trend__dot" />)}
        {chart.forecastLine && <path d={chart.forecastLine} className="trend__line trend__line--forecast" />}
        {shown && <circle cx={chart.x(shown.year)} cy={chart.y(shown.value)} r="4.5" className="trend__point" />}
      </svg>

      <div className="trend__legend">
        <span><i className="trend__swatch" />{t('panel.trendHistory')}</span>
        {chart.forecastLine && <span><i className="trend__swatch trend__swatch--forecast" />{t('panel.trendForecast')}</span>}
      </div>
    </div>
  );
}
