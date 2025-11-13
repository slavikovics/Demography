import { useState } from 'react';
import './Header.css';

function Header({ selectedLanguage, onLanguageChange, selectedModel, onModelChange }) {
  // Локализация для всех элементов
  const translations = {
    russian: {
      title: "Демография Беларуси",
      github: "Github",
      belstat: "Belstat",
      // Названия моделей
      prophet: "Prophet",
      linear: "Линейная регрессия",
      exponential: "Экспоненциальное сглаживание",
      // Языки
      russian: "Русский",
      english: "English"
    },
    english: {
      title: "Belarusian Demography",
      github: "Github",
      belstat: "Belstat",
      // Названия моделей
      prophet: "Prophet",
      linear: "Linear Regression",
      exponential: "Exponential Smoothing",
      // Языки
      russian: "Russian",
      english: "English"
    }
  };

  const t = translations[selectedLanguage] || translations.russian;

  // Массивы для выпадающих списков с локализованными названиями
  const languages = [
    { value: 'russian', label: t.russian },
    { value: 'english', label: t.english }
  ];

  const models = [
    { value: 'prophet', label: t.prophet },
    { value: 'linear', label: t.linear },
    { value: 'exponential', label: t.exponential }
  ];

  return (
    <header className="App-header">
      <h2 className="HeaderTitle">{t.title}</h2>
      
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

      <a className="Header-item" href="https://github.com/slavikovics/Demography">{t.github}</a>
      <a className="Header-item" href="https://dataportal.belstat.gov.by/osids/home-page">{t.belstat}</a>
    </header>
  );
}

export default Header;