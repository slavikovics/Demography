import React, { useState, useEffect } from 'react';

const HEADER_HEIGHT = 40; // px, adjust to your header height
const FOOTER_HEIGHT = 0; // px, adjust to your footer height

const apiUrl = process.env.REACT_APP_API_URL || 'http://localhost:5000';

function BelarusDistrictTable() {
  const [fields, setFields] = useState([]);
  const [data, setData] = useState([]);
  const [sortBy, setSortBy] = useState(null);
  const [sortOrder, setSortOrder] = useState('asc');
  const [loading, setLoading] = useState(false);

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

  const handleSort = (field) => {
    if (sortBy === field) {
      setSortOrder(sortOrder === 'asc' ? 'desc' : 'asc');
    } else {
      setSortBy(field);
      setSortOrder('asc');
    }
  };

  return (
    <div
      style={{
        padding: '2.5rem',
        background: 'white',
        borderRadius: '12px',
        maxWidth: '1000px',
        margin: '2.2rem auto',
        height: `calc(100vh - ${HEADER_HEIGHT}px - ${FOOTER_HEIGHT}px)`,
        display: 'flex',
        flexDirection: 'column'
      }}
    >
      <div style={{ flex: 1, overflow: 'auto' }}>
        <table style={{ width: '100%', borderCollapse: 'collapse' }}>
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
                <td colSpan={fields.length} style={{ textAlign: 'center', padding: '30px' }}>Loading...</td>
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
  );
}

export default BelarusDistrictTable;