import { useMemo } from 'react';
import { GeoJSON } from 'react-leaflet';
import { formatNumber, localizeUnit } from './format';

const BASE_STYLE = { color: '#2d3748', weight: 1, fillColor: '#88c', fillOpacity: 0.3 };
const NO_DATA_COLOR = '#cbd5e0';

const escapeHtml = (text) =>
  String(text).replace(/[&<>"']/g, (c) => ({ '&': '&amp;', '<': '&lt;', '>': '&gt;', '"': '&quot;', "'": '&#39;' }[c]));

/**
 * Слой районов. Без colorOf выглядит как исходная карта; с colorOf — тематическая раскраска.
 * Слой пересоздаётся при смене ключа (показатель, год, модель, язык, выбранный район).
 */
export default function DistrictLayer({
  geoJson, language, selectedId, onFeatureSelect, colorOf, values, noData, unit, layerKey,
}) {
  const colored = typeof colorOf === 'function';

  const styleFor = useMemo(() => (feature) => {
    const isSelected = selectedId !== null && feature.properties.regionId === selectedId;
    let style = BASE_STYLE;

    if (colored) {
      const value = values?.[feature.properties.regionId];
      const color = noData || value === undefined ? NO_DATA_COLOR : colorOf(value);
      style = { ...BASE_STYLE, fillColor: color || NO_DATA_COLOR, fillOpacity: 0.8, weight: 1, color: '#ffffff' };
    }

    return isSelected ? { ...style, color: '#1a365d', weight: 3, fillOpacity: Math.max(style.fillOpacity, 0.6) } : style;
  }, [colored, colorOf, values, noData, selectedId]);

  const onEachFeature = (feature, layer) => {
    const { shapeName, shapeNameRu, regionId } = feature.properties;
    const title = language === 'russian' && shapeNameRu ? shapeNameRu : shapeName;

    layer.on({
      mouseover: (event) => {
        event.target.setStyle({ weight: 3, color: '#1a365d', fillOpacity: colored ? 0.95 : 0.7 });
        event.target.bringToFront();
      },
      mouseout: (event) => event.target.setStyle(styleFor(feature)),
      click: () => { if (regionId) onFeatureSelect(feature); },
    });

    if (!title) return;

    let content = `<strong>${escapeHtml(title)}</strong>`;
    if (colored && !noData && values?.[regionId] !== undefined) {
      const unitText = localizeUnit(unit, language);
      content += `<span class="district-label__value">${escapeHtml(formatNumber(values[regionId], language))}`
        + `${unitText ? ` ${escapeHtml(unitText)}` : ''}</span>`;
    }
    layer.bindTooltip(content, { sticky: true, direction: 'top', className: 'district-label', opacity: 1 });
  };

  return (
    <GeoJSON key={layerKey} data={geoJson} style={styleFor} onEachFeature={onEachFeature} />
  );
}
