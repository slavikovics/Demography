import './App.css';
import './Scrollbars.css'
import React from 'react';
import YearSlider from './YearSlider';
import Header from './Header';
import BelarusDistrictMap from './Map';
import belarusGeoJson from './belarus-districts.json';

function App() {
  const [year, setYear] = React.useState(2024);
  const [selectedLanguage, setSelectedLanguage] = React.useState('russian');
  const [selectedModel, setSelectedModel] = React.useState('prophet');

  const handleLanguageChange = (event) => {
    setSelectedLanguage(event.target.value);
    console.log('Selected language:', event.target.value);
  };

  const handleModelChange = (event) => {
    setSelectedModel(event.target.value);
    console.log('Selected model:', event.target.value);
  };

  return (
    <div className="App">
      <Header 
        selectedLanguage={selectedLanguage}
        onLanguageChange={handleLanguageChange}
        selectedModel={selectedModel}
        onModelChange={handleModelChange}
      />
      <div className="map-container">
        <BelarusDistrictMap 
          geoJson={belarusGeoJson} 
          year={year}
          language={selectedLanguage}
        />
      </div>
      <footer className='year-slider-footer'>
        <YearSlider year={year} onYearChange={setYear}/>
      </footer>
    </div>
  );
}

export default App;