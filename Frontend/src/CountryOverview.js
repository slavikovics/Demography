import React from 'react';
import './CountryOverview.css';

const apiUrl = process.env.REACT_APP_API_URL || 'http://localhost:5000';

// Локализация для разных языков
const translations = {
  russian: {
    countryName: "Республика Беларусь",
    year: "Год",
    regionId: "ID региона",
    model: "Модель",
    loading: "Загрузка данных о населении...",
    total: "Всего",
    male: "Мужчины",
    female: "Женщины",
    records: "Записи",
    noData: "Данные о населении отсутствуют",
    for: "для",
    in: "в",
    historical: "Исторические данные",
    prophet: "Prophet",
    linear: "Линейная регрессия",
    exponential: "Экспоненциальное сглаживание"
  },
  english: {
    countryName: "Republic of Belarus",
    year: "Year",
    regionId: "Region ID",
    model: "Model",
    loading: "Loading population data...",
    total: "Total",
    male: "Male",
    female: "Female",
    records: "Records",
    noData: "No population data available",
    for: "for",
    in: "in",
    historical: "Historical data",
    prophet: "Prophet",
    linear: "Linear regression",
    exponential: "Exponential smoothing"
  }
};

export default function CountryOverview({ year, language = 'russian', selectedModel = 'prophet' }) {
  const [countryData, setCountryData] = React.useState(null);
  const [loading, setLoading] = React.useState(false);

  // Получаем переводы для выбранного языка
  const t = translations[language] || translations.russian;

  // Функция для получения локализованного названия модели
  const getLocalizedModelName = (model) => {
    switch (model) {
      case 'historical': return t.historical;
      case 'prophet': return t.prophet;
      case 'linear': return t.linear;
      case 'exponential': return t.exponential;
      default: return model;
    }
  };

  React.useEffect(() => {
    const fetchCountryData = async () => {
      setLoading(true);
      try {
        // Добавляем параметр model в запрос
        const url = `${apiUrl}/population/?territory_id=699961&year=${year}&model=${selectedModel}`;
        const response = await fetch(url);
        
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
  }, [year, selectedModel]); // Добавляем selectedModel в зависимости

  const getGenderClass = (gender) => {
    switch (gender?.toLowerCase()) {
      case 'male': return 'gender-male';
      case 'female': return 'gender-female';
      case 'total': return 'gender-total';
      default: return '';
    }
  };

  // Функция для локализации названия пола
  const getLocalizedGender = (gender) => {
    const genderLower = gender?.toLowerCase();
    switch (genderLower) {
      case 'male':
      case 'males':
        return t.male;
      case 'female':
      case 'females':
        return t.female;
      case 'total':
        return t.total;
      default:
        return gender;
    }
  };

  const totalPopulation = countryData
    ?.filter(record => record.gender === 'Total' || record.gender === 'Total Population')
    ?.reduce((sum, record) => sum + record.people, 0) || 0;

  const malePopulation = countryData
    ?.filter(record => record.gender === 'Males' || record.gender === 'Male')
    ?.reduce((sum, record) => sum + record.people, 0) || 0;

  const femalePopulation = countryData
    ?.filter(record => record.gender === 'Females' || record.gender === 'Female')
    ?.reduce((sum, record) => sum + record.people, 0) || 0;

  return (
    <div className="country-overview-container">
      <div className="country-overview-popup">
        <div className="country-overview-header">
          <h4>{t.countryName}</h4>
          <div className="country-overview-meta">
            <div className="meta-item">
              <strong>{t.year}:</strong> {year}
            </div>
            <div className="meta-item">
              <strong>{t.regionId}:</strong> 699961
            </div>
          </div>
        </div>

        <div className="country-overview-content">
          {loading ? (
            <div className="loading-state">
              <div className="loading-spinner"></div>
              <p>{t.loading}</p>
            </div>
          ) : countryData ? (
            <>
              <div className="stats-grid">
                <div className="stat-card">
                  <div className="stat-value">{totalPopulation.toLocaleString()}</div>
                  <div className="stat-label gender-total">{t.total}</div>
                </div>
                <div className="stat-card">
                  <div className="stat-value">{malePopulation.toLocaleString()}</div>
                  <div className="stat-label gender-male">{t.male}</div>
                </div>
                <div className="stat-card">
                  <div className="stat-value">{femalePopulation.toLocaleString()}</div>
                  <div className="stat-label gender-female">{t.female}</div>
                </div>
                <div className="stat-card">
                  <div className="stat-value">{countryData.length}</div>
                  <div className="stat-label">{t.records}</div>
                </div>
              </div>
            </>
          ) : (
            <div className="no-data-state">
              <div className="no-data-icon">📊</div>
              <p>{t.noData}</p>
              <p style={{ fontSize: '0.8rem', marginTop: '8px' }}>
                {t.for} {t.countryName} {t.in} {year} ({getLocalizedModelName(selectedModel)})
              </p>
            </div>
          )}
        </div>
      </div>
    </div>
  );
}