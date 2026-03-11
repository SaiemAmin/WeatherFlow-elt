WITH staging AS (
    SELECT * FROM {{ ref('stg_weather') }}
)

SELECT
    city,
    year,
    month,
    day,
    ROUND(AVG(temperature_c), 2)      AS avg_temp_c,
    ROUND(MAX(temperature_c), 2)      AS max_temp_c,
    ROUND(MIN(temperature_c), 2)      AS min_temp_c,
    ROUND(AVG(humidity_pct), 2)       AS avg_humidity_pct,
    ROUND(SUM(precipitation_mm), 2)   AS total_precipitation_mm,
    ROUND(AVG(wind_speed_kmh), 2)     AS avg_wind_speed_kmh
FROM staging
GROUP BY city, year, month, day
ORDER BY city, year, month, day
