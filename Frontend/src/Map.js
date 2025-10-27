import { MapContainer, TileLayer, GeoJSON, Popup } from "react-leaflet";
import "leaflet/dist/leaflet.css";
import { useState, useEffect, useCallback } from 'react';

export default function BelarusDistrictMap({ geoJson, year }) {
  const [selectedFeature, setSelectedFeature] = useState(null);
  const [populationData, setPopulationData] = useState(null);
  const [loading, setLoading] = useState(false);

  const districtStyle = {
    color: "#333",
    weight: 1,
    fillColor: "#88c",
    fillOpacity: 0.3,
  };

  // Memoize the fetch function
  const fetchPopulationData = useCallback(async (territoryId, year) => {
    if (!territoryId) return;
    
    setLoading(true);
    try {
      const response = await fetch(
        `http://localhost:8000/population/?territory_id=${territoryId}&year=${year}`
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
          setSelectedFeature(feature);
          // Don't fetch here anymore - the useEffect will handle it
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
      <GeoJSON 
        data={geoJson} 
        style={districtStyle} 
        onEachFeature={onEachDistrict} 
      />
      
      {/* Population Popup */}
      {selectedFeature && (
        <Popup
          position={[
            selectedFeature.geometry.coordinates[0][0][1],
            selectedFeature.geometry.coordinates[0][0][0]
          ]}
          onClose={() => {
            setSelectedFeature(null);
            setPopulationData(null);
          }}
        >
          <div className="population-popup">
            <h3>{selectedFeature.properties.shapeName}</h3>
            <p><strong>Year:</strong> {year}</p>
            <p><strong>Region ID:</strong> {selectedFeature.properties.regionId}</p>
            
            {loading ? (
              <p>Loading population data...</p>
            ) : populationData ? (
              <div className="population-stats">
                <h4>Population Statistics:</h4>
                <table style={{ width: '100%', borderCollapse: 'collapse' }}>
                  <thead>
                    <tr>
                      <th style={{ border: '1px solid #ccc', padding: '4px' }}>Gender</th>
                      <th style={{ border: '1px solid #ccc', padding: '4px' }}>Population</th>
                      <th style={{ border: '1px solid #ccc', padding: '4px' }}>Age Group</th>
                      <th style={{ border: '1px solid #ccc', padding: '4px' }}>Area Type</th>
                    </tr>
                  </thead>
                  <tbody>
                    {populationData.map((record, index) => (
                      <tr key={index}>
                        <td style={{ border: '1px solid #ccc', padding: '4px' }}>{record.gender}</td>
                        <td style={{ border: '1px solid #ccc', padding: '4px' }}>
                          {record.people.toLocaleString()}
                        </td>
                        <td style={{ border: '1px solid #ccc', padding: '4px' }}>
                          {record.age_group || 'N/A'}
                        </td>
                        <td style={{ border: '1px solid #ccc', padding: '4px' }}>
                          {record.type_of_area || 'N/A'}
                        </td>
                      </tr>
                    ))}
                  </tbody>
                </table>
                
                {/* Summary Statistics */}
                {populationData.length > 0 && (
                  <div style={{ marginTop: '10px' }}>
                    <h5>Summary:</h5>
                    <p>
                      <strong>Total Population: </strong>
                      {populationData
                        .filter(record => record.gender === 'Total')
                        .reduce((sum, record) => sum + record.people, 0)
                        .toLocaleString()}
                    </p>
                  </div>
                )}
              </div>
            ) : (
              <p>No population data available for this region and year.</p>
            )}
          </div>
        </Popup>
      )}
    </MapContainer>
  );
}