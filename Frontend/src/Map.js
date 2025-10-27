// BelarusDistrictMap.js
import { MapContainer, TileLayer } from "react-leaflet";
import "leaflet/dist/leaflet.css";
import { useState, useEffect, useCallback } from 'react';
import DistrictLayer from './DistrictLayer';
import PopulationPopup from './PopulationPopup';

const apiUrl = process.env.REACT_APP_API_URL || 'http://localhost:5000';

export default function BelarusDistrictMap({ geoJson, year }) {
  const [selectedFeature, setSelectedFeature] = useState(null);
  const [populationData, setPopulationData] = useState(null);
  const [loading, setLoading] = useState(false);

  const fetchPopulationData = useCallback(async (territoryId, year) => {
    if (!territoryId) return;
    
    setLoading(true);
    try {
      const response = await fetch(
        `${apiUrl}/population/?territory_id=${territoryId}&year=${year}`
      );
      if (response.ok) {
        const data = await response.json();
        setPopulationData(data);
      } else {
        console.error('Failed to fetch population data');
        setPopulationData(null);
      }
    } catch (error) {
      console.error('Error fetching population data:', error);
      setPopulationData(null);
    }
    setLoading(false);
  }, []);

  // Refetch data when year changes and a feature is selected
  useEffect(() => {
    if (selectedFeature) {
      const regionId = selectedFeature.properties.regionId;
      fetchPopulationData(regionId, year);
    }
  }, [year, selectedFeature, fetchPopulationData]);

  const handleFeatureSelect = (feature) => {
    setSelectedFeature(feature);
  };

  const handlePopupClose = () => {
    setSelectedFeature(null);
    setPopulationData(null);
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
      
      <DistrictLayer 
        geoJson={geoJson}
        onFeatureSelect={handleFeatureSelect}
      />
      
      <PopulationPopup
        selectedFeature={selectedFeature}
        populationData={populationData}
        loading={loading}
        year={year}
        onClose={handlePopupClose}
      />
    </MapContainer>
  );
}