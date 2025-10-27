function YearSlider({ year, onYearChange }) {
  const minYear = 2010;
  const maxYear = 2034;
  const years = Array.from({ length: maxYear - minYear + 1 }, (_, i) => minYear + i);

  return (
    <div className="year-slider-container">
      <div className="year-slider">    
        <div className="slider-container">
          <div className="slider-wrapper">
          </div>
          <input
            type="range"
            id="year"
            min={minYear}
            max={maxYear}
            value={year}
            onChange={(e) => onYearChange(parseInt(e.target.value))}
            className="slider-input"
          />
          <div className="slider-ticks">
            {years.map((currentYear) => (
              <div 
                key={currentYear} 
                className={`slider-tick ${currentYear === year ? 'active' : ''}`}
                style={{ 
                  left: `${((currentYear - minYear) / (maxYear - minYear)) * 100}%` 
                }}
              >
                <span className="tick-label">{currentYear}</span>
              </div>
            ))}
          </div>
        </div>
    
      </div>
    </div>
  );
}

export default YearSlider;