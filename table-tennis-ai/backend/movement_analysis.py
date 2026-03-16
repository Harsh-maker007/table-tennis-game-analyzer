from __future__ import annotations

from typing import Dict, List, Tuple
from pathlib import Path
import math

import cv2
import mediapipe as mp
from mediapipe.tasks import python
from mediapipe.tasks.python import vision


def _avg_speed_angle(
    points: List[dict],
    frame_size: Tuple[int, int],
    scale_x: float,
    scale_y: float,
    fps: float,
) -> Tuple[float, float]:
    if len(points) < 2:
        return 0.0, 0.0
    total_speed = 0.0
    vx = 0.0
    vy = 0.0
    count = 0
    width, height = frame_size
    for i in range(1, len(points)):
        p0 = points[i - 1]
        p1 = points[i]
        dt = max(1, int(p1["frame"]) - int(p0["frame"]))
        dx_px = (p1["x"] - p0["x"]) * width
        dy_px = (p1["y"] - p0["y"]) * height
        dist_m = math.sqrt((dx_px * scale_x) ** 2 + (dy_px * scale_y) ** 2)
        speed_mps = dist_m / (dt / fps)
        total_speed += speed_mps
        dist = math.sqrt(dx_px * dx_px + dy_px * dy_px)
        if dist > 0:
            vx += dx_px / dist
            vy += dy_px / dist
        count += 1
    avg_speed_mps = total_speed / count if count else 0.0
    avg_speed_kmh = avg_speed_mps * 3.6
    avg_angle = math.degrees(math.atan2(vy, vx)) if (vx or vy) else 0.0
    return avg_speed_kmh, avg_angle


def analyze_movement(
    video_path: str,
    pose_model_path: str | Path,
    hand_model_path: str | Path,
    frame_size: Tuple[int, int],
    scale_x: float,
    scale_y: float,
    fps: float,
    frame_stride: int = 3,
) -> Dict[str, object]:
    cap = cv2.VideoCapture(video_path)
    if not cap.isOpened():
        raise ValueError(f"Unable to open video: {video_path}")

    pose_model_path = Path(pose_model_path)
    hand_model_path = Path(hand_model_path)
    if not pose_model_path.exists() or not hand_model_path.exists():
        cap.release()
        return {
            "movement_points": [],
            "left_pct": 0.0,
            "right_pct": 0.0,
            "hands": {"left": [], "right": [], "left_speed": 0.0, "right_speed": 0.0},
            "feet": {"left": [], "right": [], "left_speed": 0.0, "right_speed": 0.0},
        }

    base_pose = python.BaseOptions(model_asset_path=str(pose_model_path))
    pose_options = vision.PoseLandmarkerOptions(
        base_options=base_pose,
        running_mode=vision.RunningMode.VIDEO,
        num_poses=1,
    )
    pose_landmarker = vision.PoseLandmarker.create_from_options(pose_options)

    base_hand = python.BaseOptions(model_asset_path=str(hand_model_path))
    hand_options = vision.HandLandmarkerOptions(
        base_options=base_hand,
        running_mode=vision.RunningMode.VIDEO,
        num_hands=2,
    )
    hand_landmarker = vision.HandLandmarker.create_from_options(hand_options)

    fps = fps or (cap.get(cv2.CAP_PROP_FPS) or 30.0)
    frame_idx = 0

    hip_points: List[Tuple[float, float]] = []
    left_count = 0
    right_count = 0

    hands_left: List[dict] = []
    hands_right: List[dict] = []
    feet_left: List[dict] = []
    feet_right: List[dict] = []

    while True:
        ret, frame = cap.read()
        if not ret:
            break
        if frame_idx % frame_stride != 0:
            frame_idx += 1
            continue

        rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
        image = mp.Image(image_format=mp.ImageFormat.SRGB, data=rgb)
        ts_ms = int((frame_idx / fps) * 1000)

        pose_result = pose_landmarker.detect_for_video(image, ts_ms)
        if pose_result.pose_landmarks:
            lm = pose_result.pose_landmarks[0]
            hip = lm[23]
            hip_points.append((hip.x, hip.y))
            if hip.x < 0.5:
                left_count += 1
            else:
                right_count += 1

            left_ankle = lm[27]
            right_ankle = lm[28]
            feet_left.append({"x": left_ankle.x, "y": left_ankle.y, "frame": frame_idx})
            feet_right.append({"x": right_ankle.x, "y": right_ankle.y, "frame": frame_idx})

            left_wrist = lm[15]
            right_wrist = lm[16]
            hands_left.append({"x": left_wrist.x, "y": left_wrist.y, "frame": frame_idx})
            hands_right.append({"x": right_wrist.x, "y": right_wrist.y, "frame": frame_idx})

        hand_result = hand_landmarker.detect_for_video(image, ts_ms)
        if hand_result.hand_landmarks and hand_result.handedness:
            for i, hand_lm in enumerate(hand_result.hand_landmarks):
                handed = hand_result.handedness[i][0].category_name
                wrist = hand_lm[0]
                if handed.lower() == "left":
                    hands_left.append({"x": wrist.x, "y": wrist.y, "frame": frame_idx})
                else:
                    hands_right.append({"x": wrist.x, "y": wrist.y, "frame": frame_idx})

        frame_idx += 1

    cap.release()
    total = left_count + right_count
    left_pct = (left_count / total * 100.0) if total else 0.0
    right_pct = (right_count / total * 100.0) if total else 0.0

    hand_left_speed, hand_left_angle = _avg_speed_angle(
        hands_left, frame_size, scale_x, scale_y, fps
    )
    hand_right_speed, hand_right_angle = _avg_speed_angle(
        hands_right, frame_size, scale_x, scale_y, fps
    )
    foot_left_speed, foot_left_angle = _avg_speed_angle(
        feet_left, frame_size, scale_x, scale_y, fps
    )
    foot_right_speed, foot_right_angle = _avg_speed_angle(
        feet_right, frame_size, scale_x, scale_y, fps
    )

    return {
        "movement_points": hip_points,
        "left_pct": left_pct,
        "right_pct": right_pct,
        "hands": {
            "left": hands_left,
            "right": hands_right,
            "left_speed": hand_left_speed,
            "right_speed": hand_right_speed,
            "left_angle": hand_left_angle,
            "right_angle": hand_right_angle,
        },
        "feet": {
            "left": feet_left,
            "right": feet_right,
            "left_speed": foot_left_speed,
            "right_speed": foot_right_speed,
            "left_angle": foot_left_angle,
            "right_angle": foot_right_angle,
        },
    }
