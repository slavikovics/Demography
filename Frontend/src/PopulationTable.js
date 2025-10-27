// PopulationTable.js
export default function PopulationTable({ populationData }) {
  const totalPopulation = populationData
    .filter(record => record.gender === 'Total')
    .reduce((sum, record) => sum + record.people, 0);

  return (
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
      
      {populationData.length > 0 && (
        <div style={{ marginTop: '10px' }}>
          <p>
            <strong>Total Population: </strong>
            {totalPopulation.toLocaleString()}
          </p>
        </div>
      )}
    </div>
  );
}