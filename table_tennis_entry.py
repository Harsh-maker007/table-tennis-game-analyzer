from pathlib import Path
import os
import urllib.request

import sys

ROOT = Path(__file__).resolve().parent
BACKEND_ROOT = ROOT / "table-tennis-ai"
sys.path.append(str(BACKEND_ROOT))

from backend.video_processor import analyze_video


MODEL_PATH = BACKEND_ROOT / "models" / "yolov8_table_tennis.pt"
MP_MODELS = BACKEND_ROOT / "models" / "mediapipe"
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


def analyze_video_file(video_path: str):
    model_path = _ensure_model(MODEL_PATH, TMP_MODEL, YOLO_FALLBACK_URL)
    pose_path = _ensure_model(POSE_MODEL, TMP_POSE, POSE_URL)
    hand_path = _ensure_model(HAND_MODEL, TMP_HAND, HAND_URL)
    frame_stride = int(os.getenv("TTAI_FRAME_STRIDE", "8"))
    max_frames = int(os.getenv("TTAI_MAX_FRAMES", "450"))
    return analyze_video(
        video_path,
        model_path,
        class_id=32,
        pose_model_path=pose_path,
        hand_model_path=hand_path,
        frame_stride=frame_stride,
        max_frames=max_frames,
    )
