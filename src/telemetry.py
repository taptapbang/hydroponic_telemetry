# src/telemetry.py

#FastAPI Implementation
#Real time telemetry and data retrieval from postgres, created from Atlas sensor readings
#The goal is to be lean, since this is running on an rpi5
#We use REST for historical data, websockets for live monitoring

# 7/12 - updated for postgres

#deprecated imports commented out
import logging
import io
import zipfile
import csv
import os


from anyio.streams import file
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse
from pydantic import BaseModel
from psycopg2.extras import RealDictCursor
from pathlib import Path
from contextlib import contextmanager

from database import get_db_connection

#import os
#import csv
#import asyncio
#from collections import deque
#from fastapi import FastAPI, WebSocket, WebSocketDisconnect

"""phase 2 cv implementation import notes
#import glob
#from fastapi import HTTPException - ****done
#from fastapi.responses import FileResponse
"""

#LOG_FILE = os.path.expanduser("~/nft_monitor/src/hydro_log.csv") -deprecated

#PHOTOS = #directory to be used later

#API logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s [API] %(message)s')
app = FastAPI(title="Hydroponic Telemetry API")

#frontend connections config
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

"""deprecated
#csv reading, prototype implementation. Ideally we'd be reading postgres
def get_telemetry_data(limit: int = 100) -> list:

    try:
        with open(LOG_FILE, mode='r', newline='') as log_file:
            reader = csv.DictReader(log_file)
            return list(deque(reader, maxlen=limit))
    except Exception as e:
        logging.error(e)
        return []
        """

#***Load calc file - keeping sql queries from main code***

CALC_FILE = Path(__file__).parent / "series_calc.sql"
try:
    with open(CALC_FILE, mode='r') as file:
        CALC_QUERY = file.read()
except FileNotFoundError:
    logging.error(f"Could not find {CALC_FILE}")

#Payload validation
class DataPayload(BaseModel):
    crop_id: int = 1 #active crop id = bus
    temperature: float | None = None
    ph: float | None = None
    ec: float | None = None

#context manager for database connection/cursor
#see https://stackoverflow.com/questions/73314054/how-to-implement-a-context-manager-for-connections-cursors-in-python
#this handles connections, cursors, and error management.
@contextmanager
def db_connection(commit=False):
    connection = get_db_connection()
    cursor = connection.cursor(cursor_factory=RealDictCursor)
    try:
        yield cursor
        if commit:
            connection.commit()
    except Exception as e:
        if commit:
            connection.rollback()
        logging.error(f"Could not connect to database: {e}")
        raise HTTPException(status_code=500, detail=str(e))
    finally:
        cursor.close()
        connection.close()

#REST Endpoints for data delivery, data reception, and queries for the pipeline

    #takes payload and commits to db
@app.post("/api/v1/telemetry/")
async def ingest_telemetry(payload: DataPayload):
    with db_connection(commit=True) as cursor:
        cursor.execute("""
        
            INSERT INTO sensor_readings (crop_id, temperature, ph, ec)
            VALUES (%s, %s, %s, %s)
                
        """, (payload.crop_id, payload.temperature, payload.ph, payload.ec))

        return {"status": "success", "message": "Telemetry recorded"}

@app.get("/api/v1/telemetry/history")
async def get_telemetry_history(limit: int = 100):

   if not CALC_QUERY:
       raise HTTPException(status_code=500, detail="File series_calc.sql missing.")

   with db_connection(commit=False) as cursor:
       #  pass the SQL string and substitute the %s with our limit
       cursor.execute(CALC_QUERY, (limit,))
       return cursor.fetchall()

#download csv zip package that contains daily log sets from the entire grow cycle
#will need to be expanded to support concurrent crop_id/buses as if multiple grows are involved
@app.get("/api/v1/telemetry/export")
def export_daily_csv_zip():
    export_dir = "exports"
    os.makedirs(export_dir, exist_ok=True)
    zip_path = os.path.join(export_dir, "hydroponics_export.zip")

    with db_connection() as cursor, zipfile.ZipFile(zip_path, "w", zipfile.ZIP_DEFLATED) as zip_file:

        cursor.execute("""
                    SELECT timestamp, temperature, ph, ec
                    FROM sensor_readings
                    ORDER BY timestamp ASC
                    """)

        current_day = None
        csv_buffer = io.StringIO()
        writer = csv.writer(csv_buffer)

        for row in cursor:
            if not row.get("timestamp"):
                continue

            day_str = row["timestamp"].strftime("%Y-%m-%d")

            if day_str != current_day:
                if current_day is not None:
                    zip_file.writestr(f"hydro_data_{current_day}.csv", csv_buffer.getvalue())

                current_day = day_str
                csv_buffer.seek(0)
                csv_buffer.truncate(0)
                writer.writerow(["Timestamp", "Temperature", "pH", "EC"])  # New header

            writer.writerow([
                row["timestamp"].strftime("%Y-%m-%d %H:%M:%S"),
                row.get("temperature", ""),
                row.get("ph", ""),
                row.get("ec", "")
            ])

        if current_day is not None:
            zip_file.writestr(f"hydro_data_{current_day}.csv", csv_buffer.getvalue())

    return FileResponse(
        path=zip_path,
        media_type="application/zip",
        filename="hydroponics_export.zip"
    )

#NOTES: vision implementation example, for later phases
# @app.get("/api/v1/vision/latest")
# async def get_latest_capture():
#
#     if not os.path.exists(PHOTOS_DIR):
#         raise HTTPException(status_code=404, detail="Vision directory not found")
#
#     search_patterns = [
#         os.path.join(PHOTOS_DIR, "processed_*.jpg"),
#         os.path.join(PHOTOS_DIR, "capture_*.jpg"),
#         os.path.join(PHOTOS_DIR, "*.jpg")
#     ]
#
#     available_files = []
#     for pattern in search_patterns:
#         available_files.extend(glob.glob(pattern))
#
#     if not available_files:
#         raise HTTPException(status_code=404, detail="No vision captures available")
#
#     latest_file = max(available_files, key=os.path.getmtime)
#     return FileResponse(latest_file, media_type="image/jpeg")

#websocket endpoint setup
"""Deprecated, websocket was used to stream from csv. Obsolete due to postgres
@app.websocket("/ws/telemetry/live")
async def telemetry_stream(websocket: WebSocket):
    await websocket.accept()
    logging.info("WebSocket client connected to live stream.")

    last_modified = 0

    try:
        while True:
            if os.path.exists(LOG_FILE):
                current_modified = os.path.getmtime(LOG_FILE)

                # File was updated by the background monitor daemon
                if current_modified > last_modified:
                    latest_record = get_telemetry_data(limit=1)
                    if latest_record:
                        await websocket.send_json(latest_record[0])
                    last_modified = current_modified

            # 1-second non-blocking pause
            await asyncio.sleep(1)

    except WebSocketDisconnect:
        logging.info("WebSocket client disconnected.")
    except Exception as e:
        logging.error(f"WebSocket exception: {e}")
"""

if __name__ == "__main__":
    import uvicorn

    print(" Hydroponic monitoring API\n docs: http://0.0.0.0:8000/docs")
    uvicorn.run("telemetry:app", host="0.0.0.0", port=8000, reload=True)