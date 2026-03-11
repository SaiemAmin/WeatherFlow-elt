import requests
import json
import boto3
from datetime import datetime

CITIES = [
    {"name": "new_york",    "lat": 40.7128,  "lon": -74.0060},
    {"name": "los_angeles", "lat": 34.0522,  "lon": -118.2437},
    {"name": "chicago",     "lat": 41.8781,  "lon": -87.6298},
]

BUCKET_NAME = "meteo-elt-project"

def fetch_weather_data(city):
    url = "https://api.open-meteo.com/v1/forecast"
    params = {
        "latitude": city["lat"],
        "longitude": city["lon"],
        "hourly": "temperature_2m,relative_humidity_2m,precipitation,wind_speed_10m,weather_code",
        "timezone": "America/New_York",
        "forecast_days": 1
    }
    response = requests.get(url, params=params)
    response.raise_for_status()
    return response.json()

def upload_to_s3(data, city_name):
    s3 = boto3.client("s3")
    now = datetime.now()
    key = (
        f"raw/weather/"
        f"city={city_name}/"
        f"year={now.year}/"
        f"month={now.month:02d}/"
        f"day={now.day:02d}/"
        f"data.json"
    )
    s3.put_object(
        Bucket=BUCKET_NAME,
        Key=key,
        Body=json.dumps(data),
        ContentType="application/json"
    )
    print(f"Uploaded {city_name} → s3://{BUCKET_NAME}/{key}")

def lambda_handler(event, context):
    for city in CITIES:
        data = fetch_weather_data(city)
        upload_to_s3(data, city["name"])
    return {
        "statusCode": 200,
        "body": "Weather data ingestion complete"
    }