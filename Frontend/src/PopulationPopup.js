// PopulationPopup.js
import { Popup } from "react-leaflet";
import PopulationTable from "./PopulationTable";

export default function PopulationPopup({ 
  selectedFeature, 
  populationData, 
  loading, 
  year, 
  onClose 
}) {
  if (!selectedFeature) return null;

  const getPopupPosition = () => {
    if (!selectedFeature?.geometry?.coordinates?.[0]?.[0]?.[0]) {
      return [53.0, 28.0]; // Default center if coordinates are invalid
    }
    return [
      selectedFeature.geometry.coordinates[0][0][1],
      selectedFeature.geometry.coordinates[0][0][0]
    ];
  };

  return (
    <Popup position={getPopupPosition()} onClose={onClose}>
      <div className="population-popup">
        <h3>{selectedFeature.properties.shapeName}</h3>
        <p><strong>Year:</strong> {year}</p>
        <p><strong>Region ID:</strong> {selectedFeature.properties.regionId}</p>
        
        {loading ? (
          <p>Loading population data...</p>
        ) : populationData ? (
          <PopulationTable populationData={populationData} />
        ) : (
          <p>No population data available for this region and year.</p>
        )}
      </div>
    </Popup>
  );
}