# src/app.py
# 7/12 - updated for postgres

#FastHTML implementation/prototype dashboard
from fasthtml.common import *
import urllib.request
import json
from datetime import datetime

#import master ui components and htmx group
from ui_components import MainDashboard, MetricsGroup

# Pointers to FastAPI
LATEST = "http://localhost:8000/api/v1/telemetry/history?limit=1"
#HISTORY = "http://localhost:8000/api/v1/telemetry/history?limit=50" deprecated, postgres queries handle this now

# app setup - pico, tailwind, chart.js
# https://www.fastht.ml/docs/ref/response_types.html

"""NOTE: Large sections of HTMX and JS code for FastHTML in this area have been abstracted to charts.js and 
ui_components.py. Initial prototype v1 included this in the app.py script, but were removed to keep code readable.
See v1 prototype for messy code.
"""

app, rt = fast_app(
    hdrs=(
        Script(src="https://cdn.tailwindcss.com"),
        Script(src="https://cdn.jsdelivr.net/npm/chart.js"),
        # Import premium fonts
        Link(href="https://fonts.googleapis.com/css2?family=Inter:wght@300;400;600&family=JetBrains+Mono:wght@400;700&display=swap", rel="stylesheet"),
        Meta(name="viewport", content="width=device-width, initial-scale=1.0"),
        # Apply the font to the whole body
        Style("body { font-family: 'Inter', sans-serif; } .font-mono { font-family: 'JetBrains Mono', monospace; }")
    )
)

#data helper
def format_val(val):
    if val is None or val == "":
        return "NA"
    return str(val)

# fetch sensor data block. Uses nexted loop to update every sensor key as data is gathered
def get_sensor_data():
    data = {
        "ph": "--", "ec": "--", "temp": "--",
        "ph_60m": "--", "ec_60m": "--", "temp_60m": "--",
        "ph_1440m": "--", "ec_1440m": "--", "temp_1440m": "--",
        "time": datetime.now().strftime("%H:%M:%S")
    }
    try:
        req = urllib.request.Request(LATEST)
        with urllib.request.urlopen(req) as response:
            if response.status == 200:
                payload = json.loads(response.read().decode())
                if payload and len(payload) > 0:
                    last_row = payload[0]

                    for key in data:
                        if key != "time":
                            data[key] = format_val(last_row.get(key))

                    timestamp = last_row.get("timestamp", "")
                    if timestamp and " " in timestamp:
                        data["time"] = timestamp.split(" ")[1]

    except Exception as e:
        print(f"FastAPI error: {e}")

    return data

#routes
@rt("/charts.js")
def serve_js():
    return FileResponse("charts.js")

@rt("/")
def get():
    return MainDashboard(get_sensor_data())

@rt("/update-metrics")
def update():
    return MetricsGroup(get_sensor_data())

if __name__ == "__main__":
    serve(port=5001)
