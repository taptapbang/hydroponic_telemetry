#FastAPI Implementation
#Real time telemetry and data retrieval for hydro_log.csv created from Atlas sensor readings
#The goal is to be lean, since this is running on an rpi5
#We use REST for historical data, websockets for live monitoring

import os
import csv
import asyncio
import logging
from collections import deque

from fastapi import FastAPI, WebSocket, WebSocketDisconnect
from fastapi.middleware.cors import CORSMiddleware

#phase 2 cv implentation import notes
#import glob
#from fastapi import HTTPException
#from fastapi.responses import FileResponse

LOG_FILE = os.path.expanduser("/verson_1/hydro_log.csv")
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

#csv reading, prototype implementation. Ideally we'd be reading postgres
def get_telemetry_data(limit: int = 100) -> list:

    try:
        with open(LOG_FILE, mode='r', newline='') as log_file:
            reader = csv.DictReader(log_file)
            return list(deque(reader, maxlen=limit))
    except Exception as e:
        logging.error(e)
        return []

#REST Endpoints/ call data for charts/histograms
@app.get("/api/v1/telemetry/history")
async def get_telemetry_history(limit: int = 100):
    return get_telemetry_data(limit)

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

@app.websocket("/ws/telemetry/live")
async def telemetry_stream(websocket: WebSocket):
    """Pushes new telemetry rows instantly when the CSV is modified."""
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


if __name__ == "__main__":
    import uvicorn

    print(" Hydroponic monitoring\n docs: http://0.0.0.0:8000/docs")
    uvicorn.run("telemetry:app", host="0.0.0.0", port=8000, reload=True)