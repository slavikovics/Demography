from fastapi import FastAPI, HTTPException, Query
from typing import List, Optional
from data_storage.database import DemographyDatabase
from models.population_record import PopulationRecord
from models.territory import Territory
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
    year: int = Query(..., description="Year to query")):
    try:
        population_data = db.get_population_by_territory_and_year(territory_id, year)
        
        if not population_data:
            raise HTTPException(
                status_code=404,
                detail=f"No population data found for territory {territory_id} in year {year}"
            )
        
        records = []
        for record_tuple in population_data:
            record = PopulationRecord.from_tuple(record_tuple)
                
            records.append(record)
        
        if not records:
            raise HTTPException(
                status_code=404,
                detail=f"No records found matching the specified filters"
            )
        
        return records
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Internal server error: {str(e)}")
    

@app.get("/population/territories/")
async def get_available_territories():
    try:
        territories = db.get_all_territories()
        territory_list = []
        
        territories = []
        for territory_tuple in territories:
            territories.append(Territory.from_tuple(territory_tuple))
        
        return {"territories": territory_list, "count": len(territory_list)}
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Internal server error: {str(e)}")
    

def main():
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)


if __name__ == "__main__":
    main()