import { MapContainer, TileLayer, GeoJSON } from "react-leaflet";
import "leaflet/dist/leaflet.css";

export default function BelarusDistrictMap({ geoJson }) {
  const districtStyle = {
    color: "#333",
    weight: 1,
    fillColor: "#88c",
    fillOpacity: 0.3,
  };

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
    });

    if (feature.properties?.name) {
      layer.bindTooltip(feature.properties.name, {
        permanent: false,
        direction: "center",
        className: "district-label",
      });
    }
  };

  return (
    <MapContainer
      center={[53.0, 28.0]}
      zoom={6}
      style={{ 
        width: "100%", 
        height: "100%",
        position: "absolute",
        top: 0,
        left: 0
      }}
      zoomControl={true}
      attributionControl={true}
    >
      <TileLayer url="https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png" />
      <GeoJSON data={geoJson} style={districtStyle} onEachFeature={onEachDistrict} />
    </MapContainer>
  );
}