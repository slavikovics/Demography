// DistrictLayer.js
import { GeoJSON } from "react-leaflet";

const districtStyle = {
  color: "#333",
  weight: 1,
  fillColor: "#88c",
  fillOpacity: 0.3,
};

export default function DistrictLayer({ geoJson, onFeatureSelect }) {
  const onEachDistrict = (feature, layer) => {
    layer.on({
      mouseover: (e) => {
        e.target.setStyle({
          fillColor: "#E6F0FF",
          fillOpacity: 0.7,
          weight: 2
        });
      },
      mouseout: (e) => {
        e.target.setStyle(districtStyle);
      },
      click: (e) => {
        const regionId = feature.properties.regionId;
        if (regionId) {
          onFeatureSelect(feature);
        }
      }
    });

    if (feature.properties?.shapeName) {
      layer.bindTooltip(feature.properties.shapeName, {
        permanent: false,
        direction: "center",
        className: "district-label",
      });
    }
  };

  return (
    <GeoJSON 
      data={geoJson} 
      style={districtStyle} 
      onEachFeature={onEachDistrict} 
    />
  );
}