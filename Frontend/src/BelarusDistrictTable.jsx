import React, {useState, useEffect} from 'react';

const HEADER_HEIGHT = 40;
const FOOTER_HEIGHT = 0;
const apiUrl = process.env.REACT_APP_API_URL || 'http://localhost:5000';

function BelarusDistrictTable({selectedLanguage}) {
    const [fields, setFields] = useState([]);
    const [data, setData] = useState([]);
    const [sortBy, setSortBy] = useState(null);
    const [sortOrder, setSortOrder] = useState('asc');
    const [loading, setLoading] = useState(false);
    const [interesting, setInteresting] = useState([]);

    useEffect(() => {
        fetch(`${apiUrl}/population_table/fields`)
            .then(res => res.json())
            .then(res => {
                const fieldArr = res.fields || [];
                setFields(fieldArr);
                if (fieldArr.length > 0) setSortBy(fieldArr[0]);
            });
    }, []);

    useEffect(() => {
        if (!sortBy) return;
        setLoading(true);
        fetch(`${apiUrl}/population_table/?sort_by=${sortBy}&sorting_direction=${sortOrder}`)
            .then(res => res.json())
            .then(res => {
                setData(res);
                setLoading(false);
            })
            .catch(() => setLoading(false));
    }, [sortBy, sortOrder]);

    useEffect(() => {
        fetch(`${apiUrl}/population_table/interesting_data`)
            .then(res => res.json())
            .then(res => setInteresting(res.fields || []));
    }, []);

    const handleSort = (field) => {
        if (sortBy === field) {
            setSortOrder(sortOrder === 'asc' ? 'desc' : 'asc');
        } else {
            setSortBy(field);
            setSortOrder('asc');
        }
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
        <div
            style={{
                marginTop: HEADER_HEIGHT,
                height: `calc(100vh - ${HEADER_HEIGHT}px - ${FOOTER_HEIGHT}px)`,
                width: '100%',
                display: 'flex',
                flexDirection: 'row',
                justifyContent: 'flex-start', // <-- FIX
                boxSizing: 'border-box',
                alignItems: 'flex-start'
            }}
        >


        {/* Sidebar with interesting data */}
            <div style={{
                flexBasis: '25%',
                maxWidth: '25%',
                background: '#f8fafc',
                borderRadius: '12px',
                margin: '2rem 0 2rem 2rem',
                padding: '1.5rem',
                boxShadow: '0 2px 12px rgba(0,0,0,0.07)',
                fontSize: '1rem',
                display: 'flex',
                flexDirection: 'column',
                gap: '1.2rem'
            }}>
                <h3 style={{marginBottom: '1rem'}}>{t.interesting}</h3>
                {interesting.length === 4 ? (
                    <>
                        <div>
                            <strong>{t.min}:</strong><br/>
                            {interesting[0][0] && (
                                <span>
                  {interesting[0][0][langIdx]} : {interesting[0][0][2]}
                </span>
                            )}
                        </div>
                        <div>
                            <strong>{t.max}:</strong><br/>
                            {interesting[1][0] && (
                                <span>
                  {interesting[1][0][langIdx]} : {interesting[1][0][2]}
                </span>
                            )}
                        </div>
                        <div>
                            <strong>{t.lowGrowth}:</strong><br/>
                            {interesting[2][0] && (
                                <span>
                  {interesting[2][0][langIdx]} : {interesting[2][0][2]}
                </span>
                            )}
                        </div>
                        <div>
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
            {/* Table aligned right */}
            <div style={{
                flexBasis: '75%',
                maxWidth: '75%',
                marginLeft: 'auto',        // <-- FIX: это правильно прижмёт блок вправо
                display: 'flex',
                alignItems: 'center',      // Center vertically
                justifyContent: 'center',  // Center horizontally
                height: '100%',
            }}>
                <div
                    style={{
                        padding: '2.5rem',
                        background: 'white',
                        borderRadius: '12px',
                        margin: '2.2rem 2rem 2.2rem 0', // было OK, но можно сделать margin: '2.2rem'
                        height: '100%',
                        display: 'flex',
                        flexDirection: 'column',
                        boxSizing: 'border-box'
                    }}
                >
                    <div style={{flex: 1, overflow: 'auto', width: '150%', margin: '0 auto'}}>
                        <table style={{width: '100%', borderCollapse: 'collapse'}}>
                            <thead>
                            <tr>
                                {fields.map(col => (
                                    <th
                                        key={col}
                                        onClick={() => handleSort(col)}
                                        style={{
                                            cursor: 'pointer',
                                            padding: '10px',
                                            background: '#f8fafc',
                                            borderBottom: '2px solid #e2e8f0',
                                            position: 'sticky',
                                            top: 0,
                                            zIndex: 2
                                        }}
                                    >
                                        {col.replace('_', ' ').replace('people', 'Население').replace('name', 'Название')}
                                        {sortBy === col ? (sortOrder === 'asc' ? ' ▲' : ' ▼') : ''}
                                    </th>
                                ))}
                            </tr>
                            </thead>
                            <tbody>
                            {loading ? (
                                <tr>
                                    <td colSpan={fields.length}
                                        style={{textAlign: 'center', padding: '30px'}}>Loading...
                                    </td>
                                </tr>
                            ) : (
                                data.map((row, idx) => (
                                    <tr
                                        key={idx}
                                        style={{
                                            background: idx % 2 === 0 ? '#fff' : '#f3f4f6'
                                        }}
                                    >
                                        {fields.map(col => (
                                            <td key={col}>{row[col]}</td>
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
    );
}

export default BelarusDistrictTable;