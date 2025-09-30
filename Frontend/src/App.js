import './App.css';
import React from 'react';
import YearSlider from './YearSlider';
import Header from './Header';
import BelarusDistrictMap from './Map';
import belarusGeoJson from './belarus-districts.json';

function App() {
  const [year, setYear] = React.useState(2020);
  
  return (
    <div className="App">
      <Header/>
      <div className="map-container">
        <BelarusDistrictMap geoJson={belarusGeoJson}/>
      </div>
      <footer className='year-slider-footer'>
        <YearSlider year={year} onYearChange={setYear}/>
      </footer>
    </div>
  );
}

export default App;