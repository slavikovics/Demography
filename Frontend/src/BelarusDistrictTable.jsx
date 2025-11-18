import React, {useState, useEffect} from 'react';
import './BelarusDistrictTable.css';

const apiUrl = process.env.REACT_APP_API_URL || 'http://localhost:5000';

function BelarusDistrictTable({selectedLanguage, year, selectedModel}) {
    const [data, setData] = useState([]);
    const [sortBy, setSortBy] = useState('people');
    const [sortOrder, setSortOrder] = useState('desc');
    const [loading, setLoading] = useState(false);
    const [interesting, setInteresting] = useState([]);

    // Статические колонки
    const fields = [
        { key: 'id', labelRu: 'ID', labelEn: 'ID' },
        { key: 'name_ru', labelRu: 'Название', labelEn: 'Name' },
        { key: 'name_en', labelRu: 'Название (англ.)', labelEn: 'Name (English)' },
        { key: 'people', labelRu: 'Население', labelEn: 'Population' }
    ];

    useEffect(() => {
        if (!sortBy) return;
        setLoading(true);
        fetch(`${apiUrl}/population_table/?year=${year}&model=${selectedModel}&sort_by=${sortBy}&sorting_direction=${sortOrder}`)
            .then(res => res.json())
            .then(res => {
                setData(res);
                setLoading(false);
            })
            .catch(() => setLoading(false));
    }, [sortBy, sortOrder, year, selectedModel]);

    useEffect(() => {
        fetch(`${apiUrl}/population_table/interesting_data/?year=${year}&model=${selectedModel}`)
            .then(res => res.json())
            .then(res => setInteresting(res.fields || []));
    }, [year, selectedModel]);

    const handleSort = (fieldKey) => {
        if (sortBy === fieldKey) {
            setSortOrder(sortOrder === 'asc' ? 'desc' : 'asc');
        } else {
            setSortBy(fieldKey);
            setSortOrder('asc');
        }
    };

    const getFieldLabel = (field) => {
        return selectedLanguage === 'english' ? field.labelEn : field.labelRu;
    };

    const labels = {
        russian: {
            interesting: "Интересные данные",
            min: "Минимальное население",
            max: "Максимальное население",
            lowGrowth: "Минимальный прирост",
            highGrowth: "Максимальный прирост"
        },
        english: {
            interesting: "Interesting Data",
            min: "Min Population",
            max: "Max Population",
            lowGrowth: "Lowest Growth",
            highGrowth: "Highest Growth"
        }
    };
    const t = labels[selectedLanguage] || labels.russian;
    const langIdx = selectedLanguage === 'english' ? 1 : 0;

    return (
        <div className="table-page-container">
            <div className="table-main-container">
                {/* Sidebar with interesting data */}
                <div className="table-sidebar">
                    <h3>{t.interesting}</h3>
                    {interesting.length === 4 ? (
                        <>
                            <div className="data-item">
                                <strong>{t.min}:</strong><br/>
                                {interesting[0][0] && (
                                    <span>
                                        {interesting[0][0][langIdx]} : {interesting[0][0][2]}
                                    </span>
                                )}
                            </div>
                            <div className="data-item">
                                <strong>{t.max}:</strong><br/>
                                {interesting[1][0] && (
                                    <span>
                                        {interesting[1][0][langIdx]} : {interesting[1][0][2]}
                                    </span>
                                )}
                            </div>
                            <div className="data-item">
                                <strong>{t.lowGrowth}:</strong><br/>
                                {interesting[2][0] && (
                                    <span>
                                        {interesting[2][0][langIdx]} : {interesting[2][0][2]}
                                    </span>
                                )}
                            </div>
                            <div className="data-item">
                                <strong>{t.highGrowth}:</strong><br/>
                                {interesting[3][0] && (
                                    <span>
                                        {interesting[3][0][langIdx]} : {interesting[3][0][2]}
                                    </span>
                                )}
                            </div>
                        </>
                    ) : (
                        <span>Loading...</span>
                    )}
                </div>

                {/* Main table content */}
                <div className="table-content-area">
                    <div className="table-wrapper">
                        <div className="table-scroll-container">
                            <table className="data-table">
                                <thead>
                                    <tr>
                                        {fields.map(field => (
                                            <th
                                                key={field.key}
                                                onClick={() => handleSort(field.key)}
                                                className="table-header"
                                            >
                                                {getFieldLabel(field)}
                                                {sortBy === field.key ? (sortOrder === 'asc' ? ' ▲' : ' ▼') : ''}
                                            </th>
                                        ))}
                                    </tr>
                                </thead>
                                <tbody>
                                    {loading ? (
                                        <tr>
                                            <td colSpan={fields.length} className="loading-cell">
                                                Loading...
                                            </td>
                                        </tr>
                                    ) : (
                                        data.map((row, idx) => (
                                            <tr
                                                key={idx}
                                                className={idx % 2 === 0 ? 'even-row' : 'odd-row'}
                                            >
                                                {fields.map(field => (
                                                    <td key={field.key}>
                                                        {field.key === 'people' && row[field.key] 
                                                            ? row[field.key].toLocaleString() 
                                                            : row[field.key]}
                                                    </td>
                                                ))}
                                            </tr>
                                        ))
                                    )}
                                </tbody>
                            </table>
                        </div>
                    </div>
                </div>
            </div>
        </div>
    );
}

export default BelarusDistrictTable;