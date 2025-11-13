import './App.css';
import './Scrollbars.css'
import React from 'react';
import YearSlider from './YearSlider';
import Header from './Header';
import BelarusDistrictMap from './Map';
import belarusGeoJson from './belarus-districts.json';
import BelarusDistrictTable from './BelarusDistrictTable';

function App() {
    const [year, setYear] = React.useState(2024);
    const [selectedLanguage, setSelectedLanguage] = React.useState('russian');
    const [selectedModel, setSelectedModel] = React.useState('prophet');
    const [selectedTab, setSelectedTab] = React.useState('map');
    const [tableMode, setTableMode] = React.useState('total'); // 'total', 'gender', 'all'

    const handleLanguageChange = (event) => setSelectedLanguage(event.target.value);
    const handleModelChange = (event) => setSelectedModel(event.target.value);
    const handleTabChange = (event) => setSelectedTab(event.target.value);
    const handleTableModeChange = (event) => setTableMode(event.target.value);

    return (
        <div className="App">
            <Header
                selectedLanguage={selectedLanguage}
                onLanguageChange={handleLanguageChange}
                selectedModel={selectedModel}
                onModelChange={handleModelChange}
                selectedTab={selectedTab}
                onTabChange={handleTabChange}
            />
            <div className="map-container">
                {selectedTab === 'map' ? (
                    <BelarusDistrictMap
                        geoJson={belarusGeoJson}
                        year={year}
                        selectedModel={selectedModel}
                        language={selectedLanguage}
                    />
                ) : (
                    <BelarusDistrictTable
                        mode={tableMode}
                        onModeChange={handleTableModeChange}
                    />
                )}
            </div>
            <footer className='year-slider-footer'>
                {selectedTab === 'map' && (
                    <YearSlider year={year} onYearChange={setYear}/>
                )}
            </footer>
        </div>
    );
}

export default App;