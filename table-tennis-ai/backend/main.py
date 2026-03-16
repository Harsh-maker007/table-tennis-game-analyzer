from __future__ import annotations

from pathlib import Path
import os
import urllib.request

from fastapi import FastAPI, UploadFile
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse

from backend.video_processor import analyze_video


ROOT = Path(__file__).resolve().parent.parent
UPLOAD_DIR = Path(os.getenv("TMPDIR", "/tmp")) / "ttai_uploads"
MODEL_PATH = ROOT / "models" / "yolov8_table_tennis.pt"
MP_MODELS = ROOT / "models" / "mediapipe"
POSE_MODEL = MP_MODELS / "pose_landmarker_lite.task"
HAND_MODEL = MP_MODELS / "hand_landmarker.task"

TMP_DIR = Path(os.getenv("TMPDIR", "/tmp")) / "ttai"
TMP_DIR.mkdir(parents=True, exist_ok=True)
TMP_MODEL = TMP_DIR / "yolov8_table_tennis.pt"
TMP_POSE = TMP_DIR / "pose_landmarker_lite.task"
TMP_HAND = TMP_DIR / "hand_landmarker.task"

YOLO_FALLBACK_URL = (
    "https://github.com/ultralytics/assets/releases/download/v0.0.0/yolov8n.pt"
)
POSE_URL = "https://storage.googleapis.com/mediapipe-models/pose_landmarker/pose_landmarker_lite/float16/1/pose_landmarker_lite.task"
HAND_URL = "https://storage.googleapis.com/mediapipe-models/hand_landmarker/hand_landmarker/float16/1/hand_landmarker.task"


def _ensure_model(local_path: Path, fallback_path: Path, url: str) -> Path:
    if local_path.exists():
        return local_path
    if fallback_path.exists():
        return fallback_path
    try:
        urllib.request.urlretrieve(url, str(fallback_path))
        return fallback_path
    except Exception:
        return local_path
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
    model_path = _ensure_model(MODEL_PATH, TMP_MODEL, YOLO_FALLBACK_URL)
    pose_path = _ensure_model(POSE_MODEL, TMP_POSE, POSE_URL)
    hand_path = _ensure_model(HAND_MODEL, TMP_HAND, HAND_URL)

    frame_stride = int(os.getenv("TTAI_FRAME_STRIDE", "5"))
    max_frames = int(os.getenv("TTAI_MAX_FRAMES", "600"))

    result = analyze_video(
        path,
        model_path,
        class_id=32,
        pose_model_path=pose_path,
        hand_model_path=hand_path,
        frame_stride=frame_stride,
        max_frames=max_frames,
    )
    try:
        path.unlink(missing_ok=True)
    except Exception:
        pass
    return result
