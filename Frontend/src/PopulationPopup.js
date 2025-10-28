import { Popup } from "react-leaflet";

export default function PopulationPopup({ 
  selectedFeature, 
  populationData, 
  loading, 
  year, 
  onClose,
  showDetailedData = true
}) {
  if (!selectedFeature) return null;

  const getPopupPosition = () => {
    if (!selectedFeature?.geometry?.coordinates?.[0]?.[0]?.[0]) {
      return [53.0, 28.0];
    }
    return [
      selectedFeature.geometry.coordinates[0][0][1],
      selectedFeature.geometry.coordinates[0][0][0]
    ];
  };

  const getGenderClass = (gender) => {
    switch (gender?.toLowerCase()) {
      case 'male': return 'gender-male';
      case 'female': return 'gender-female';
      case 'total': return 'gender-total';
      default: return '';
    }
  };

  const totalPopulation = populationData
    ?.filter(record => record.gender === 'Total')
    ?.reduce((sum, record) => sum + record.people, 0) || 0;

  const malePopulation = populationData
    ?.filter(record => record.gender === 'Males')
    ?.reduce((sum, record) => sum + record.people, 0) || 0;

  const femalePopulation = populationData
    ?.filter(record => record.gender === 'Females')
    ?.reduce((sum, record) => sum + record.people, 0) || 0;

  return (
    <Popup 
      position={getPopupPosition()} 
      onClose={onClose}
      className="custom-popup"
    >
      <div className="population-popup">
        <div className="population-popup-header">
          <h3>{selectedFeature.properties.shapeName}</h3>
          <div className="population-popup-meta">
            <div className="meta-item">
              <strong>Year:</strong> {year}
            </div>
            <div className="meta-item">
              <strong>Region ID:</strong> {selectedFeature.properties.regionId}
            </div>
          </div>
        </div>

        <div className="population-popup-content">
          {loading ? (
            <div className="loading-state">
              <div className="loading-spinner"></div>
              <p>Loading population data...</p>
            </div>
          ) : populationData ? (
            <>
              <div className="stats-grid">
                <div className="stat-card">
                  <div className="stat-value">{totalPopulation.toLocaleString()}</div>
                  <div className="stat-label gender-total">Total</div>
                </div>
                <div className="stat-card">
                  <div className="stat-value">{malePopulation.toLocaleString()}</div>
                  <div className="stat-label gender-male">Male</div>
                </div>
                <div className="stat-card">
                  <div className="stat-value">{femalePopulation.toLocaleString()}</div>
                  <div className="stat-label gender-female">Female</div>
                </div>
                <div className="stat-card">
                  <div className="stat-value">{populationData.length}</div>
                  <div className="stat-label">Records</div>
                </div>
              </div>

              {/* Conditional rendering based on showDetailedData prop */}
              {showDetailedData && populationData.length > 0 && (
                <div className="data-section">
                  <div className="section-title">Detailed Breakdown</div>
                  <table className="population-table">
                    <thead>
                      <tr>
                        <th>Gender</th>
                        <th>Population</th>
                        <th>Age Group</th>
                      </tr>
                    </thead>
                    <tbody>
                      {populationData.slice(0, 10).map((record, index) => (
                        <tr key={index}>
                          <td className={getGenderClass(record.gender)}>
                            {record.gender}
                          </td>
                          <td>{record.people.toLocaleString()}</td>
                          <td>{record.age_group || 'All'}</td>
                        </tr>
                      ))}
                    </tbody>
                  </table>
                  {populationData.length > 10 && (
                    <div style={{ 
                      textAlign: 'center', 
                      fontSize: '0.8rem', 
                      color: '#64748b', 
                      marginTop: '12px' 
                    }}>
                      +{populationData.length - 10} more records
                    </div>
                  )}
                </div>
              )}
            </>
          ) : (
            <div className="no-data-state">
              <div className="no-data-icon">📊</div>
              <p>No population data available</p>
              <p style={{ fontSize: '0.8rem', marginTop: '8px' }}>
                for {selectedFeature.properties.shapeName} in {year}
              </p>
            </div>
          )}
        </div>
      </div>
    </Popup>
  );
}