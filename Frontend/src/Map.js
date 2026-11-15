import { useMemo, useState } from 'react';
import { MapContainer, TileLayer, ZoomControl } from 'react-leaflet';
import 'leaflet/dist/leaflet.css';
import DistrictLayer from './DistrictLayer';
import DistrictPanel from './DistrictPanel';
import CountryCard from './CountryCard';
import IndicatorLegend from './IndicatorLegend';
import { POPULATION } from './config';
import { useIndicatorValues } from './hooks';
import { buildColorScale, indicatorName, isSigned } from './indicators';
import './Map.css';

// Границы Беларуси: карта сразу показывает страну целиком в любом размере окна
const BELARUS_BOUNDS = [[51.2, 23.1], [56.2, 32.8]];

export default function BelarusDistrictMap({
  t, geoJson, year, model, language, indicators, indicator, source,
}) {
  const [selectedFeature, setSelectedFeature] = useState(null);

  const indicatorMode = indicator !== POPULATION;
  const indicatorMeta = indicators.find((item) => item.code === indicator);
  const data = useIndicatorValues(indicatorMode ? indicator : null, year, model);
  const signed = isSigned(indicator);

  const regionIds = useMemo(
    () => geoJson.features.map((feature) => feature.properties.regionId).filter(Boolean),
    [geoJson]
  );

  const colorScale = useMemo(
    () => buildColorScale(data.values, signed, regionIds),
    [data.values, signed, regionIds]
  );

  const indicatorInfo = indicatorMode && indicatorMeta ? {
    code: indicator,
    name: indicatorName(indicatorMeta, language),
    unit: data.unit,
    values: data.values,
    noData: data.noData || Boolean(data.error),
    signed,
  } : null;

  const selectedId = selectedFeature?.properties.regionId ?? null;
  const layerKey = [indicator, year, model, language, selectedId, data.loading ? 'loading' : 'ready'].join('|');

  return (
    <div className={`map-stage${selectedFeature ? ' map-stage--panel' : ''}`}>
      <MapContainer
        bounds={BELARUS_BOUNDS}
        boundsOptions={{ padding: [24, 24] }}
        minZoom={5}
        maxBounds={[[48.5, 18], [59, 38]]}
        zoomSnap={0.25}
        zoomControl={false}
        attributionControl={false}
        className="map-canvas"
      >
        <TileLayer url="https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png" />
        <ZoomControl position="bottomright" />
        <DistrictLayer
          geoJson={geoJson}
          language={language}
          selectedId={selectedId}
          onFeatureSelect={setSelectedFeature}
          layerKey={layerKey}
          {...(indicatorMode ? {
            colorOf: colorScale.colorOf,
            values: data.values,
            noData: indicatorInfo?.noData,
            unit: data.unit,
          } : {})}
        />
      </MapContainer>

      <div className="map-overlay map-overlay--left">
        <CountryCard t={t} language={language} year={year} model={model}
                     indicatorInfo={indicatorInfo} source={source} />
        {indicatorInfo && !data.loading && (
          <IndicatorLegend t={t} language={language} name={indicatorInfo.name} unit={indicatorInfo.unit}
                           buckets={colorScale.buckets} noData={indicatorInfo.noData} year={year} signed={signed} />
        )}
      </div>

      {selectedFeature ? (
        <div className="map-overlay map-overlay--right">
          <DistrictPanel t={t} language={language} feature={selectedFeature} year={year} model={model}
                         indicatorInfo={indicatorInfo} regionIds={regionIds} source={source}
                         onClose={() => setSelectedFeature(null)} />
        </div>
      ) : (
        <div className="map-hint" role="note">{t('panel.hint')}</div>
      )}
    </div>
  );
}
