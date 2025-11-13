import { Popup } from "react-leaflet";

// Локализация для разных языков
const translations = {
  russian: {
    loading: "Загрузка данных о населении...",
    year: "Год",
    regionId: "ID региона",
    total: "Всего",
    male: "Мужчины",
    female: "Женщины",
    records: "Записи",
    detailedBreakdown: "Детальная разбивка",
    gender: "Пол",
    population: "Население",
    ageGroup: "Возрастная группа",
    noData: "Данные о населении отсутствуют",
    for: "для",
    moreRecords: "еще записей",
    all: "Все",
    allAges: "Все возраста"
  },
  english: {
    loading: "Loading population data...",
    year: "Year",
    regionId: "Region ID",
    total: "Total",
    male: "Male",
    female: "Female",
    records: "Records",
    detailedBreakdown: "Detailed Breakdown",
    gender: "Gender",
    population: "Population",
    ageGroup: "Age Group",
    noData: "No population data available",
    for: "for",
    moreRecords: "more records",
    all: "All",
    allAges: "All ages"
  }
};

export default function PopulationPopup({ 
  selectedFeature, 
  populationData, 
  loading, 
  year, 
  onClose,
  showDetailedData = true,
  language = 'russian'
}) {
  if (!selectedFeature) return null;

  // Получаем переводы для выбранного языка
  const t = translations[language] || translations.russian;

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
      case 'male': 
      case 'males': 
        return 'gender-male';
      case 'female': 
      case 'females': 
        return 'gender-female';
      case 'total': 
        return 'gender-total';
      default: 
        return '';
    }
  };

  // Функция для локализации названия пола
  const getLocalizedGender = (gender) => {
    const genderLower = gender?.toLowerCase();
    switch (genderLower) {
      case 'males':
        return t.male;
      case 'females':
        return t.female;
      case 'total':
        return t.total;
      default:
        return gender;
    }
  };

  // Функция для локализации возрастной группы
  const getLocalizedAgeGroup = (ageGroup) => {
    if (ageGroup === 'By all age' || ageGroup === 'All ages' || !ageGroup) {
      return t.allAges;
    }
    return ageGroup;
  };

  const totalPopulation = populationData
    ?.filter(record => record.gender === 'Total' || record.gender === 'Total Population')
    ?.reduce((sum, record) => sum + record.people, 0) || 0;

  const malePopulation = populationData
    ?.filter(record => record.gender === 'Males' || record.gender === 'Male')
    ?.reduce((sum, record) => sum + record.people, 0) || 0;

  const femalePopulation = populationData
    ?.filter(record => record.gender === 'Females' || record.gender === 'Female')
    ?.reduce((sum, record) => sum + record.people, 0) || 0;

  return (
    <Popup 
      position={getPopupPosition()} 
      onClose={onClose}
      className="custom-popup"
    >
      <div className="population-popup">
        <div className="population-popup-header">
          <h3>
            {language === 'russian' && selectedFeature.properties.shapeNameRu
              ? selectedFeature.properties.shapeNameRu
              : selectedFeature.properties.shapeName}
          </h3>
          <div className="population-popup-meta">
            <div className="meta-item">
              <strong>{t.year}:</strong> {year}
            </div>
            <div className="meta-item">
              <strong>{t.regionId}:</strong> {selectedFeature.properties.regionId}
            </div>
          </div>
        </div>

        <div className="population-popup-content">
          {loading ? (
            <div className="loading-state">
              <div className="loading-spinner"></div>
              <p>{t.loading}</p>
            </div>
          ) : populationData ? (
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
                  <div className="stat-value">{populationData.length}</div>
                  <div className="stat-label">{t.records}</div>
                </div>
              </div>

              {/* Conditional rendering based on showDetailedData prop */}
              {showDetailedData && populationData.length > 0 && (
                <div className="data-section">
                  <div className="section-title">{t.detailedBreakdown}</div>
                  <table className="population-table">
                    <thead>
                      <tr>
                        <th>{t.gender}</th>
                        <th>{t.population}</th>
                        <th>{t.ageGroup}</th>
                      </tr>
                    </thead>
                    <tbody>
                      {populationData.slice(0, 10).map((record, index) => (
                        <tr key={index}>
                          <td className={getGenderClass(record.gender)}>
                            {getLocalizedGender(record.gender)}
                          </td>
                          <td>{record.people.toLocaleString()}</td>
                          <td>{getLocalizedAgeGroup(record.age_group)}</td>
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
                      +{populationData.length - 10} {t.moreRecords}
                    </div>
                  )}
                </div>
              )}
            </>
          ) : (
            <div className="no-data-state">
              <div className="no-data-icon">📊</div>
              <p>{t.noData}</p>
              <p style={{ fontSize: '0.8rem', marginTop: '8px' }}>
                {t.for} {selectedFeature.properties.shapeName} {year}
              </p>
            </div>
          )}
        </div>
      </div>
    </Popup>
  );
}