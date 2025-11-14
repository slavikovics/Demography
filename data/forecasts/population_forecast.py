from typing import List
import pandas as pd
import numpy as np
from prophet import Prophet
from sklearn.linear_model import LinearRegression
from statsmodels.tsa.holtwinters import ExponentialSmoothing
from data_storage.database import DemographyDatabase
from models.population_record import PopulationRecord

def create_prophet_forecast(db, territory_id, gender='Total', years_to_forecast=10, start_year=2015, end_year=2024):
    """Прогноз с использованием Prophet"""
    historical_data = []
    for year in range(start_year, end_year + 1):
        population_data = db.get_population_by_territory_and_year(territory_id, year)
        if population_data:
            for population_record in population_data:
                population = PopulationRecord.from_tuple(population_record)
                if population.gender == gender and population.model == 'historical':
                    historical_data.append({'ds': str(year), 'y': population.people})
                    break

    if len(historical_data) < 3:
        print(f"Not enough data for territory {territory_id} for Prophet")
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

def create_linear_forecast(db, territory_id, gender='Total', years_to_forecast=10, start_year=2015, end_year=2024):
    """Прогноз с использованием линейной регрессии"""
    historical_data = []
    for year in range(start_year, end_year + 1):
        population_data = db.get_population_by_territory_and_year(territory_id, year)
        if population_data:
            for population_record in population_data:
                population = PopulationRecord.from_tuple(population_record)
                if population.gender == gender and population.model == 'historical':
                    historical_data.append({'year': year, 'population': population.people})
                    break

    if len(historical_data) < 2:
        print(f"Not enough data for territory {territory_id} for Linear Regression")
        return None

    df = pd.DataFrame(historical_data)
    df = df.sort_values('year')

    X = df['year'].values.reshape(-1, 1)
    y = df['population'].values

    model = LinearRegression()
    model.fit(X, y)

    future_years = np.array([end_year + i for i in range(1, years_to_forecast + 1)]).reshape(-1, 1)
    y_pred = model.predict(future_years)

    forecast_df = pd.DataFrame({
        'ds': [str(year) for year in future_years.flatten()],
        'yhat': y_pred,
        'yhat_lower': y_pred,  # Для простоты используем те же значения
        'yhat_upper': y_pred
    })

    return forecast_df

def create_exponential_forecast(db, territory_id, gender='Total', years_to_forecast=10, start_year=2015, end_year=2024):
    """Прогноз с использованием экспоненциального сглаживания"""
    historical_data = []
    for year in range(start_year, end_year + 1):
        population_data = db.get_population_by_territory_and_year(territory_id, year)
        if population_data:
            for population_record in population_data:
                population = PopulationRecord.from_tuple(population_record)
                if population.gender == gender and population.model == 'historical':
                    historical_data.append({'year': year, 'population': population.people})
                    break

    if len(historical_data) < 3:
        print(f"Not enough data for territory {territory_id} for Exponential Smoothing")
        return None

    df = pd.DataFrame(historical_data)
    df = df.sort_values('year')

    population_series = df['population'].values

    try:
        model = ExponentialSmoothing(population_series, trend='add', seasonal=None)
        model_fit = model.fit()
        forecast = model_fit.forecast(steps=years_to_forecast)
    except:
        forecast = [np.mean(population_series)] * years_to_forecast

    future_years = [end_year + i for i in range(1, years_to_forecast + 1)]

    forecast_df = pd.DataFrame({
        'ds': [str(year) for year in future_years],
        'yhat': forecast,
        'yhat_lower': forecast,  # Для простоты используем те же значения
        'yhat_upper': forecast
    })

    return forecast_df

def create_population_forecast(db, territory_id, gender='Total', model_type='prophet', years_to_forecast=10, start_year=2015, end_year=2024):
    """Основная функция для создания прогноза с выбором модели"""
    if model_type == 'prophet':
        return create_prophet_forecast(db, territory_id, gender, years_to_forecast, start_year, end_year)
    elif model_type == 'linear':
        return create_linear_forecast(db, territory_id, gender, years_to_forecast, start_year, end_year)
    elif model_type == 'exponential':
        return create_exponential_forecast(db, territory_id, gender, years_to_forecast, start_year, end_year)
    else:
        raise ValueError(f"Unknown model type: {model_type}")

def forecast_to_population_records(territory_id: int, gender: str, forecast_df, model_type: str, age_group: str = 'By all age', type_of_area: str = 'By all types') -> List[PopulationRecord]:
    """Конвертация прогноза в записи населения с указанием модели"""
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
            type_of_area=type_of_area,
            model=model_type
        )
        
        population_records.append(population_record)
    
    return population_records

def save_forecast_to_db(db: DemographyDatabase, forecast, territory_id, gender, model_type):
    """Сохранение прогноза в базу данных с указанием модели"""
    population_records = forecast_to_population_records(
        territory_id=territory_id,
        gender=gender,
        forecast_df=forecast,
        model_type=model_type
    )
    
    population_tuples = []
    print(f'\n\n Forecast for: {territory_id} {gender} using {model_type}')
    print(forecast)
    for record in population_records:
        population_tuple = record.to_tuple()
        population_tuples.append(population_tuple)

    db.insert_population_records(population_tuples)

def build_population_forecasts_for_all_districts(model_types=None):
    """Построение прогнозов для всех районов с использованием указанных моделей"""
    if model_types is None:
        model_types = ['prophet', 'linear', 'exponential']
        
    db = DemographyDatabase()
    districts = db.get_all_available_territory_ids_for_population_forecast()

    for model_type in model_types:
        print(f"\n=== Building forecasts using {model_type} model ===")
        for district in districts:
            for gender in ['Total', 'Males', 'Females']:
                try:
                    forecast = create_population_forecast(db, district, gender=gender, model_type=model_type)
                    if forecast is not None:
                        save_forecast_to_db(db, forecast, district, gender, model_type)
                except Exception as e:
                    print(f'Failed to create forecast for territory {district} with model {model_type}: {e}')

if __name__ == '__main__':
    build_population_forecasts_for_all_districts()