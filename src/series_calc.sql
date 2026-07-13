-- src/series_calc.sql

-- used to calculate metrics needed for data collection and reporting

WITH calculated AS (

    SELECT

        to_char(timestamp AT TIME ZONE 'UTC' AT TIME ZONE current_setting('TimeZone'), 'YYYY-MM-DD HH24:MI:SS') as timestamp,
        temperature as temp,
        ph,
        ec,
        AVG(temperature) OVER w60 as temp_avg_60m,
        AVG(ph) OVER w60 as ph_avg_60m,
        AVG(ec) OVER w60 as ec_avg_60m,
        AVG(temperature) OVER w1440 as temp_avg_1440m,
        AVG(ph) OVER w1440 as ph_avg_1440m,
        AVG(ec) OVER w1440 as ec_avg_1440m

    FROM sensor_readings
    WHERE crop_id = 1
    WINDOW
        w60 AS (ORDER BY timestamp ROWS BETWEEN 11 PRECEDING AND CURRENT ROW),
        w1440 AS (ORDER BY timestamp ROWS BETWEEN 287 PRECEDING AND CURRENT ROW)
)

SELECT * FROM calculated
ORDER BY timestamp DESC
LIMIT %s;