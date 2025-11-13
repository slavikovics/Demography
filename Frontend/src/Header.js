import { useState } from 'react';
import './Header.css';

function Header() {
  const [selectedLanguage, setSelectedLanguage] = useState('russian');
  const [selectedModel, setSelectedModel] = useState('prophet');

  const languages = [
    { value: 'russian', label: 'Русский' },
    { value: 'english', label: 'English' }
  ];

  const models = [
    { value: 'prophet', label: 'Prophet' },
    { value: 'linear', label: 'Линейная регрессия' },
    { value: 'exponential', label: 'Экспоненциальное сглаживание' }
  ];

  const handleLanguageChange = (event) => {
    setSelectedLanguage(event.target.value);
    console.log('Selected language:', event.target.value);
  };

  const handleModelChange = (event) => {
    setSelectedModel(event.target.value);
    console.log('Selected model:', event.target.value);
  };

  return (
    <header className="App-header">
      <h2 className="HeaderTitle">Belarusian Demography</h2>
      
      <div className="header-controls">
        <div className="comboBox-container compact">
          <select 
            id="language-select"
            className="comboBox compact"
            value={selectedLanguage}
            onChange={handleLanguageChange}
          >
            {languages.map(lang => (
              <option key={lang.value} value={lang.value}>
                {lang.label}
              </option>
            ))}
          </select>
        </div>

        <div className="comboBox-container compact">
          <select 
            id="model-select"
            className="comboBox compact"
            value={selectedModel}
            onChange={handleModelChange}
          >
            {models.map(model => (
              <option key={model.value} value={model.value}>
                {model.label}
              </option>
            ))}
          </select>
        </div>
      </div>

      <a className="Header-item" href="https://github.com/slavikovics/Demography">Github</a>
      <a className="Header-item" href="https://dataportal.belstat.gov.by/osids/home-page">Belstat</a>
    </header>
  );
}

export default Header;