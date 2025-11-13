from fastapi import FastAPI, HTTPException, Query
from typing import List, Optional
from data_storage.database import DemographyDatabase
from models.population_record import PopulationRecord
from models.territory import Territory
from models.table_record import TableRecord
from fastapi.middleware.cors import CORSMiddleware

app = FastAPI(
    title="Demography API",
    description="API for accessing population data and forecasts",
    version="1.0.0"
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
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
        sort_by: Optional[str] = Query(None, description="Sort by field"),
        sorting_direction: Optional[str] = Query("asc", description="Sorting direction: 'asc' or 'desc'")
):
    try:
        population_table = db.get_population_table(sort_by, sorting_direction)
        records = []
        for record_tuple in population_table:
            record = TableRecord.from_tuple(record_tuple)
            records.append(record)

        # Возвращаем словари для корректной сериализации в JSON
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
async def get_interesting_data():
    try:
        fields = db.get_interesting_data()
        return {"fields": fields}
    except Exception as e:
        print(e)
        raise HTTPException(status_code=500, detail=f"Internal server error: {str(e)}")

def main():
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=5000)

if __name__ == "__main__":
    main()