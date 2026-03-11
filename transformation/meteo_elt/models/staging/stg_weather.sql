WITH source AS (
    SELECT * FROM {{ source('meteo_raw', 'weather') }}
),

flattened AS (
    SELECT 
        city, 
        year,
        month,
        day,
        hourly.time[index]                  AS hour_timestamp,
        hourly.temperature_2m[index]        AS temperature_c,
        hourly.relative_humidity_2m[index]  AS humidity_pct,
        hourly.precipitation[index]         AS precipitation_mm,
        hourly.wind_speed_10m[index]        AS wind_speed_kmh,
        hourly.weather_code[index]          AS weather_code

    FROM source
    
    CROSS JOIN UNNEST(sequence(1, 24)) AS t(index)
)

SELECT * FROM flattened
