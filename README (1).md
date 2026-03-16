# WeatherFlow — Serverless ELT Weather Pipeline 🌤️

A fully automated, serverless ELT pipeline on AWS that ingests daily historical weather data for 3 US cities, transforms it into analytics-ready tables, and visualizes it in a Power BI dashboard — running daily without manual intervention.

---

## Dashboard

Built with Power BI Desktop connected to AWS Athena via ODBC. Displays daily weather metrics for New York, Los Angeles, and Chicago with interactive city and date range filters.

![WeatherFlow Dashboard](assets/dashboard.png)

---

## Architecture

```
Open-Meteo API (free, no key needed)
        ↓
AWS Lambda (ingestion script)
        ↓
Amazon S3 (raw data lake)
  raw/weather/city=new_york/year=2026/month=03/day=11/data.json
        ↓
AWS Glue Crawler (schema detection)
        ↓
AWS Glue Data Catalog (meteo_raw database)
        ↓
Amazon Athena (queryable raw tables)
        ↓
dbt Core (transformation)
  staging layer → flattens nested JSON arrays
  curated layer → daily aggregations per city
        ↓
Amazon Athena (clean analytics-ready tables)
```

### Automation
```
8:00am UTC  → EventBridge triggers Lambda → yesterday's data lands in S3
8:30am UTC  → GitHub Actions triggers dbt run → clean tables refreshed
             → Power BI connects to Athena via ODBC → dashboard updated
             → CloudWatch monitors Lambda errors
             → SNS email alert if pipeline fails
```

---

## Tech Stack

| Layer | Tool |
|---|---|
| Ingestion | Python, AWS Lambda, boto3 |
| Storage | Amazon S3 |
| Cataloging | AWS Glue Crawler, Glue Data Catalog |
| Querying | Amazon Athena |
| Transformation | dbt Core, dbt-athena-community |
| Orchestration | AWS EventBridge, GitHub Actions |
| Monitoring | AWS CloudWatch, Amazon SNS |
| Visualization | Power BI Desktop |
| Version Control | Git, GitHub |

---

## Project Structure

```
meteo-elt-project/
├── .github/
│   └── workflows/
│       └── dbt_run.yml          # GitHub Actions workflow for dbt
├── ingestion/
│   ├── lambda_function.py       # Lambda ingestion script
│   └── requirements.txt         # Python dependencies
├── transformation/
│   └── meteo_elt/
│       ├── dbt_project.yml      # dbt project config
│       ├── models/
│       │   ├── sources.yml      # raw Athena table declaration
│       │   ├── staging/
│       │   │   └── stg_weather.sql       # flattens nested JSON
│       │   └── marts/
│       │       └── mart_daily_weather.sql # daily aggregations
│       └── macros/
│           └── generate_schema_name.sql  # custom schema routing
└── .gitignore
```

---

## Data Flow

### Extract
Python script calls the [Open-Meteo Archive API](https://open-meteo.com/) — free, no API key required. Fetches yesterday's completed historical data for 3 US cities:
- New York
- Los Angeles
- Chicago

### Variables pulled per city:
| Variable | Description |
|---|---|
| `temperature_2m` | Air temperature at 2m height (°C) |
| `relative_humidity_2m` | Humidity percentage |
| `precipitation` | Rain/snow in mm |
| `wind_speed_10m` | Wind speed at 10m height (km/h) |
| `weather_code` | WMO weather condition code |

### Load
Raw JSON landed into S3 with Hive-style partitioning:
```
s3://meteo-elt-project/raw/weather/
  city=new_york/year=2026/month=03/day=11/data.json
  city=chicago/year=2026/month=03/day=11/data.json
  ...
```

### Transform (dbt)

**Staging layer** (`stg.stg_weather`):
- Unnests hourly arrays using `CROSS JOIN UNNEST(sequence(1, 24))`
- Flattens 3 nested city rows → 72 flat rows (1 per city per hour)
- Renames columns for readability

**Curated layer** (`curated.mart_daily_weather`):
- Aggregates hourly data into daily summaries per city
- Columns: `avg_temp_c`, `max_temp_c`, `min_temp_c`, `avg_humidity_pct`, `total_precipitation_mm`, `avg_wind_speed_kmh`

---

## dbt Model Lineage

```
[source: meteo_raw.weather]
        ↓
[stg_weather]          → view in stg schema
        ↓
[mart_daily_weather]   → table in curated schema
```

---

## AWS Services Used & Cost

| Service | Usage | Cost |
|---|---|---|
| S3 | Raw JSON storage, ~few MB/day | Free tier |
| Lambda | 1 invocation/day, ~4 seconds | Free tier |
| EventBridge | 1 scheduled rule | Free tier |
| Glue Crawler | 1 run/day | Free tier |
| Athena | Few KB scanned per query | Free tier |
| CloudWatch | 1 alarm | Free tier |
| SNS | Email on failure only | Free tier |
| **Total** | | **$0/month** |

---

## IAM Setup

### IAM User (for local development)
Permissions:
- `AmazonS3FullAccess`
- `AmazonAthenaFullAccess`
- `AWSGlueConsoleFullAccess`
- `CloudWatchLogsReadOnlyAccess`

### IAM Role for Lambda (`AWSGlueServiceRole-meteo`)
- `AWSGlueServiceRole`
- Scoped S3 inline policy for `meteo-elt-project` bucket only

---

## Environment Setup

### Local Development
```bash
# install dependencies
pip install requests boto3 dbt-athena-community

# configure AWS credentials
aws configure

# run ingestion manually
python ingestion/lambda_function.py

# run dbt transformations
cd transformation/meteo_elt
dbt debug    # test connection
dbt run      # run all models
```

### GitHub Actions Secrets Required
```
AWS_ACCESS_KEY_ID
AWS_SECRET_ACCESS_KEY
```

---

## Sample Analytics Queries

**Which city was warmest on average?**
```sql
SELECT city, avg_temp_c
FROM curated.mart_daily_weather
ORDER BY avg_temp_c DESC;
```

**Total rainfall per city this month?**
```sql
SELECT city, SUM(total_precipitation_mm) AS monthly_precip
FROM curated.mart_daily_weather
WHERE year = '2026' AND month = '03'
GROUP BY city
ORDER BY monthly_precip DESC;
```

**Coldest day recorded?**
```sql
SELECT city, year, month, day, min_temp_c
FROM curated.mart_daily_weather
ORDER BY min_temp_c ASC
LIMIT 1;
```

**Windiest city on average?**
```sql
SELECT city, ROUND(AVG(avg_wind_speed_kmh), 2) AS avg_wind
FROM curated.mart_daily_weather
GROUP BY city
ORDER BY avg_wind DESC;
```

---

## Key Concepts Demonstrated

- **ELT pattern** — raw data loaded first, transformed after landing
- **Medallion architecture** — raw → staging → curated layers
- **Serverless compute** — Lambda + EventBridge, no servers to manage
- **Infrastructure as code** — dbt models version controlled in git
- **Least privilege IAM** — scoped permissions per service
- **Partitioned data lake** — Hive-style S3 partitioning for efficient querying
- **CI/CD for data** — GitHub Actions automates dbt runs on a schedule
- **Data visualization** — Power BI connected to Athena via ODBC for live dashboarding

---

## What I Learned

This project covers every stage of the data engineering lifecycle as described in *Fundamentals of Data Engineering* by Joe Reis:

- **Source systems** → REST API ingestion from Open-Meteo Archive API
- **Storage** → S3 data lake with partitioning strategy
- **Ingestion** → batch ingestion of completed historical data, scheduled daily
- **Transformation** → ELT with dbt, staging and mart layers
- **Serving** → Athena SQL for analytics + Power BI dashboard via ODBC
- **Undercurrents** → security (IAM), orchestration (EventBridge + GitHub Actions), monitoring (CloudWatch)
