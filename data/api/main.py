from fastapi import FastAPI, HTTPException, Query
from typing import List, Optional
from data_storage.database import DemographyDatabase
from models.population_record import PopulationRecord
from models.territory import Territory
from models.table_record import TableRecord
from models.indicator_record import IndicatorRecord
from indicator_catalog import INDICATORS
from fastapi.middleware.cors import CORSMiddleware

app = FastAPI(
    title="Demography API",
    description="API for accessing population data and forecasts",
    version="1.0.0",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=False,
    allow_methods=["*"],
    allow_headers=["*"],
)

db = DemographyDatabase()

@app.get("/")
async def root():
    return {"message": "Demography API is running", "version": "1.0.0"}

@app.get("/population/")
async def get_population_records(
    territory_id: int = Query(..., description="Territory ID"),
    year: int = Query(..., description="Year to query"),
    model: Optional[str] = Query(None, description="Forecast model: 'historical', 'prophet', 'linear', 'exponential'")
):
    if year <= 2024:
        model = 'historical'

    try:
        population_data = db.get_population_by_territory_and_year(territory_id, year, model)
        
        if not population_data:
            raise HTTPException(
                status_code=404,
                detail=f"No population data found for territory {territory_id} in year {year}" + 
                       (f" with model {model}" if model else "")
            )
        
        records = []
        for record_tuple in population_data:
            record = PopulationRecord.from_tuple(record_tuple)
            records.append(record)
        
        return records

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Internal server error: {str(e)}")

@app.get("/population/models/")
async def get_available_models(
    territory_id: int = Query(..., description="Territory ID")
):
    """Получить доступные модели прогнозирования для территории"""
    try:
        models = db.get_available_models(territory_id)
        return {"territory_id": territory_id, "available_models": models}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Internal server error: {str(e)}")

@app.get("/population/territories/")
async def get_available_territories():
    try:
        territories = db.get_all_territories()
        territory_list = []
        
        for territory_tuple in territories:
            territory_list.append(Territory.from_tuple(territory_tuple))
        
        return {"territories": territory_list, "count": len(territory_list)}
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Internal server error: {str(e)}")

@app.get("/population_table/")
async def get_population_table(
        year: int = Query(...),
        model: Optional[str] = Query('historical'),
        sort_by: Optional[str] = Query(None, description="Sort by field"),
        sorting_direction: Optional[str] = Query("asc", description="Sorting direction: 'asc' or 'desc'")
):
    try:
        if year <= 2024:
            model = 'historical'

        population_table = db.get_population_table(year, model, sort_by, sorting_direction)
        records = []
        for record_tuple in population_table:
            record = TableRecord.from_tuple(record_tuple)
            records.append(record)

        return [record.to_dict() for record in records]

    except Exception as e:
        print(e)
        raise HTTPException(status_code=500, detail=f"Internal server error: {str(e)}")

@app.get("/population_table/fields")
async def get_population_table_fields():
    try:
        fields = db.get_population_table_fields()
        return {"fields": fields}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Internal server error: {str(e)}")

@app.get("/population_table/interesting_data")
async def get_interesting_data(
        year: int = Query(...),
        model: Optional[str] = Query('historical')):
    try:
        if year <= 2024:
            model = 'historical'

        fields = db.get_interesting_data(year, model)
        return {"fields": fields}
    except Exception as e:
        print(e)
        raise HTTPException(status_code=500, detail=f"Internal server error: {str(e)}")

@app.get("/indicators/")
async def get_indicators():
    """Список доступных показателей (рождаемость, смертность, миграция, браки, разводы, плотность)."""
    return {"indicators": [
        {"code": code, "key": key, "name_ru": name_ru, "name_en": name_en}
        for code, (key, name_ru, name_en) in INDICATORS.items()
    ]}


@app.get("/indicators/{indicator_code}/")
async def get_indicator_by_year(
        indicator_code: str,
        year: int = Query(..., description="Year to query"),
        model: str = Query('historical', description="'historical', 'prophet', 'linear' or 'exponential'")
):
    """Значения показателя по всем территориям за год (как опубликовано Белстатом)."""
    if indicator_code not in INDICATORS:
        raise HTTPException(status_code=404, detail=f"Unknown indicator {indicator_code}")
    try:
        rows = db.get_indicator_by_year(indicator_code, year, model)
        if not rows and model != 'historical':
            # для лет, где есть опубликованные данные, прогноз не строится
            rows = db.get_indicator_by_year(indicator_code, year, 'historical')
        if not rows:
            raise HTTPException(
                status_code=404,
                detail=f"No data for indicator {indicator_code} in year {year}. "
                       f"Historical years: {db.get_indicator_years(indicator_code)}")
        return [IndicatorRecord.from_row(row).to_dict() for row in rows]
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Internal server error: {str(e)}")


@app.get("/indicators/{indicator_code}/table/")
async def get_indicator_table(
        indicator_code: str,
        year: int = Query(..., description="Year to query"),
        model: str = Query('historical', description="'historical', 'prophet', 'linear' or 'exponential'"),
        sort_by: str = Query('name_ru', description="'id', 'name_ru', 'name_en' or 'value'"),
        sorting_direction: str = Query('asc', description="'asc' or 'desc'")
):
    """Таблица значений показателя по территориям с названиями (для фронтенда)."""
    if indicator_code not in INDICATORS:
        raise HTTPException(status_code=404, detail=f"Unknown indicator {indicator_code}")
    try:
        rows = db.get_indicator_table(indicator_code, year, model, sort_by, sorting_direction)
        if not rows and model != 'historical':
            rows = db.get_indicator_table(indicator_code, year, 'historical', sort_by, sorting_direction)
        if not rows:
            raise HTTPException(
                status_code=404,
                detail=f"No data for indicator {indicator_code} in year {year}. "
                       f"Historical years: {db.get_indicator_years(indicator_code)}")
        return [{'id': r[0], 'name_ru': (r[1] or '').replace('"', ''), 'name_en': (r[2] or '').replace('"', ''),
                 'value': r[3], 'unit': r[4]} for r in rows]
    except HTTPException:
        raise
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Internal server error: {str(e)}")


@app.get("/indicators/{indicator_code}/series/")
async def get_indicator_series(
        indicator_code: str,
        territory_id: int = Query(..., description="Territory ID"),
        model: str = Query('historical', description="'historical', 'prophet', 'linear' or 'exponential'")
):
    """Временной ряд показателя для территории. Для модели-прогноза возвращает только прогнозные годы."""
    if indicator_code not in INDICATORS:
        raise HTTPException(status_code=404, detail=f"Unknown indicator {indicator_code}")
    try:
        rows = db.get_indicator_series(indicator_code, territory_id, model)
        if not rows:
            raise HTTPException(
                status_code=404,
                detail=f"No data for indicator {indicator_code} and territory {territory_id}")
        return [IndicatorRecord.from_row(row).to_dict() for row in rows]
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Internal server error: {str(e)}")


def main():
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=5000)

if __name__ == "__main__":
    main()