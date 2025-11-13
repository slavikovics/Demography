import { useState } from 'react';
import './Header.css';

function Header({ selectedLanguage, onLanguageChange, selectedModel, onModelChange }) {
  const languages = [
    { value: 'russian', label: 'Русский' },
    { value: 'english', label: 'English' }
  ];

  const models = [
    { value: 'prophet', label: 'Prophet' },
    { value: 'linear', label: 'Линейная регрессия' },
    { value: 'exponential', label: 'Экспоненциальное сглаживание' }
  ];

  // Локализация для заголовка
  const titleTranslations = {
    russian: "Демография Беларуси",
    english: "Belarusian Demography"
  };

  const headerTitle = titleTranslations[selectedLanguage] || titleTranslations.english;

  return (
    <header className="App-header">
      <h2 className="HeaderTitle">{headerTitle}</h2>
      
      <div className="header-controls">
        <div className="comboBox-container compact">
          <select 
            id="language-select"
            className="comboBox compact"
            value={selectedLanguage}
            onChange={onLanguageChange}
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
            onChange={onModelChange}
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