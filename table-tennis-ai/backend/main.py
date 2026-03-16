from __future__ import annotations

from pathlib import Path

from fastapi import FastAPI, UploadFile
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse

from backend.video_processor import analyze_video


ROOT = Path(__file__).resolve().parent.parent
UPLOAD_DIR = ROOT / "uploads"
MODEL_PATH = ROOT / "models" / "yolov8_table_tennis.pt"
MP_MODELS = ROOT / "models" / "mediapipe"
POSE_MODEL = MP_MODELS / "pose_landmarker_lite.task"
HAND_MODEL = MP_MODELS / "hand_landmarker.task"
FRONTEND_DIR = ROOT / "frontend"

app = FastAPI()
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.mount("/static", StaticFiles(directory=FRONTEND_DIR), name="static")


@app.get("/")
def index():
    return FileResponse(FRONTEND_DIR / "index.html")


@app.post("/analyze")
async def analyze(video: UploadFile):
    UPLOAD_DIR.mkdir(parents=True, exist_ok=True)
    path = UPLOAD_DIR / video.filename
    with path.open("wb") as f:
        f.write(await video.read())

    # COCO class id 32 = sports ball for yolov8n.pt baseline model.
    result = analyze_video(
        path,
        MODEL_PATH,
        class_id=32,
        pose_model_path=POSE_MODEL,
        hand_model_path=HAND_MODEL,
    )
    return result
