import React from 'react';
import './CountryOverview.css';

const apiUrl = process.env.REACT_APP_API_URL || 'http://localhost:5000';

export default function CountryOverview({ year }) {
  const [countryData, setCountryData] = React.useState(null);
  const [loading, setLoading] = React.useState(false);

  React.useEffect(() => {
    const fetchCountryData = async () => {
      setLoading(true);
      try {
        const response = await fetch(
          `${apiUrl}/population/?territory_id=699961&year=${year}`
        );
        if (response.ok) {
          const data = await response.json();
          setCountryData(data);
        } else {
          setCountryData(null);
        }
      } catch (error) {
        console.error('Error fetching country data:', error);
        setCountryData(null);
      }
      setLoading(false);
    };

    fetchCountryData();
  }, [year]);

  const getGenderClass = (gender) => {
    switch (gender?.toLowerCase()) {
      case 'male': return 'gender-male';
      case 'female': return 'gender-female';
      case 'total': return 'gender-total';
      default: return '';
    }
  };

  const totalPopulation = countryData
    ?.filter(record => record.gender === 'Total')
    ?.reduce((sum, record) => sum + record.people, 0) || 0;

  const malePopulation = countryData
    ?.filter(record => record.gender === 'Males')
    ?.reduce((sum, record) => sum + record.people, 0) || 0;

  const femalePopulation = countryData
    ?.filter(record => record.gender === 'Females')
    ?.reduce((sum, record) => sum + record.people, 0) || 0;

  return (
    <div className="country-overview-container">
      <div className="country-overview-popup">
        <div className="country-overview-header">
          <h4>Republic of Belarus</h4>
          <div className="country-overview-meta">
            <div className="meta-item">
              <strong>Year:</strong> {year}
            </div>
            <div className="meta-item">
              <strong>Region ID:</strong> 699961
            </div>
          </div>
        </div>

        <div className="country-overview-content">
          {loading ? (
            <div className="loading-state">
              <div className="loading-spinner"></div>
              <p>Loading population data...</p>
            </div>
          ) : countryData ? (
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
                  <div className="stat-value">{countryData.length}</div>
                  <div className="stat-label">Records</div>
                </div>
              </div>
            </>
          ) : (
            <div className="no-data-state">
              <div className="no-data-icon">📊</div>
              <p>No population data available</p>
              <p style={{ fontSize: '0.8rem', marginTop: '8px' }}>
                for Republic of Belarus in {year}
              </p>
            </div>
          )}
        </div>
      </div>
    </div>
  );
}