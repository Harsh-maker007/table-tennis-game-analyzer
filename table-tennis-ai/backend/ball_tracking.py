from __future__ import annotations

from pathlib import Path
from typing import List, Tuple, Dict

import cv2
from ultralytics import YOLO


def _load_model(model_path: str | Path) -> YOLO:
    path = Path(model_path)
    if not path.exists():
        raise FileNotFoundError(
            f"YOLO model not found at '{path}'. Place yolov8_table_tennis.pt in models/."
        )
    return YOLO(str(path))


def track_ball(
    video_path: str | Path,
    model_path: str | Path,
    class_id: int = 0,
    frame_stride: int = 5,
    max_frames: int = 600,
) -> Tuple[List[Dict[str, int]], Tuple[int, int], float]:
    model = _load_model(model_path)
    cap = cv2.VideoCapture(str(video_path))
    if not cap.isOpened():
        raise ValueError(f"Unable to open video: {video_path}")

    width = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH))
    height = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
    frame_size = (width, height)
    fps = cap.get(cv2.CAP_PROP_FPS) or 30.0

    ball_positions: List[Dict[str, int]] = []
    frame_idx = 0
    processed = 0
    while True:
        ret, frame = cap.read()
        if not ret:
            break
        if frame_idx % frame_stride != 0:
            frame_idx += 1
            continue
        processed += 1
        if processed > max_frames:
            break
        results = model(frame)
        for box in results[0].boxes:
            cls = int(box.cls[0])
            if cls == class_id:
                x1, y1, x2, y2 = box.xyxy[0]
                cx = int((x1 + x2) / 2)
                cy = int((y1 + y2) / 2)
                ball_positions.append({"frame": frame_idx, "x": cx, "y": cy})
                break
        frame_idx += 1

    cap.release()
    return ball_positions, frame_size, float(fps)
