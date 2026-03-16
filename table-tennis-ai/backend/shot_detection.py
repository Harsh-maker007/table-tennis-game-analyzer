from __future__ import annotations

from typing import Dict, List


def detect_shots(ball_positions: List[dict], min_gap_frames: int = 8) -> List[int]:
    shots: List[int] = []
    last_frame = -min_gap_frames
    for i, item in enumerate(ball_positions):
        frame = int(item.get("frame", i))
        if frame - last_frame >= min_gap_frames:
            shots.append(i)
            last_frame = frame
    return shots


def calculate_success(shots: List[Dict[str, str]]) -> float:
    total = len(shots)
    if not total:
        return 0.0
    success = sum(1 for s in shots if s.get("result") == "win")
    return (success / total) * 100.0
