from typing import List
import pandas as pd
from prophet import Prophet
from data_storage.database import DemographyDatabase
from models.population_record import PopulationRecord

def create_population_forecast(db, territory_id, gender='Total', years_to_forecast=10, start_year=2015, end_year=2024):
    historical_data = []
    for year in range(start_year, end_year + 1):
        population_data = db.get_population_by_territory_and_year(territory_id, year)
        if population_data:
            for population_record in population_data:
                population = PopulationRecord.from_tuple(population_record)
                if population.gender == gender:
                    historical_data.append({'ds': str(year), 'y': population.people})
                    break

    if len(historical_data) < 3:
        print(f"Not enough data for territory {territory_id}")
        return None
    
    df = pd.DataFrame(historical_data)
    
    model = Prophet(
        yearly_seasonality=True,
        changepoint_prior_scale=0.05,
        seasonality_prior_scale=10.0
    )
    model.fit(df)
    
    future_years = [str(end_year + i) for i in range(1, years_to_forecast + 1)]
    future = pd.DataFrame({'ds': future_years})
    
    forecast = model.predict(future)
    
    return forecast[['ds', 'yhat', 'yhat_lower', 'yhat_upper']]


def forecast_to_population_records(territory_id: int, gender: str, forecast_df, age_group: str = 'By all age', type_of_area: str = 'By all types') -> List[PopulationRecord]:
    population_records = []
    
    for _, row in forecast_df.iterrows():
        year = int(str(row['ds'])[:4])
        
        people = int(round(row['yhat']))
        
        population_record = PopulationRecord(
            territory_id=territory_id,
            gender=gender,
            people=people,
            year=year,
            age_group=age_group,
            type_of_area=type_of_area
        )
        
        population_records.append(population_record)
    
    return population_records


def save_forecast_to_db(db: DemographyDatabase, forecast, territory_id, gender):
    population_records = forecast_to_population_records(territory_id=territory_id,
                                                        gender=gender,
                                                        forecast_df=forecast)
    
    population_tuples = []
    print(f'\n\n Forecast for: {territory_id} {gender}')
    print(forecast)
    for record in population_records:
        population_tuple = record.to_tuple()
        #print(population_tuple)
        population_tuples.append(population_tuple)

    db.insert_population_records(population_tuples)


def build_population_forecasts_for_all_districts():
    db = DemographyDatabase()
    districts = db.get_all_available_territory_ids_for_population_forecast()

    for district in districts:
        for gender in ['Total', 'Males', 'Females']:

            try:
                forecast = create_population_forecast(db, district, gender=gender)
                save_forecast_to_db(db, forecast, district, gender)
            except:
                print(f'Failed to create forecast for territory {district}')

if __name__ == '__main__':
    build_population_forecasts_for_all_districts()