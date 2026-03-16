from __future__ import annotations

from typing import Dict, List, Tuple


def analyze_zones(
    ball_positions: List[dict],
    frame_size: Tuple[int, int],
    rows: int = 3,
    cols: int = 3,
) -> Dict[str, int]:
    width, height = frame_size
    if width <= 0 or height <= 0:
        return {}

    zones: Dict[str, int] = {}
    for r in range(rows):
        for c in range(cols):
            zones[f"{chr(65 + r)}{c + 1}"] = 0

    cell_w = width / cols
    cell_h = height / rows

    for item in ball_positions:
        x = int(item.get("x", -1))
        y = int(item.get("y", -1))
        label = zone_label(x, y, frame_size, rows=rows, cols=cols)
        if label:
            zones[label] += 1

    return zones


def zone_label(
    x: int,
    y: int,
    frame_size: Tuple[int, int],
    rows: int = 3,
    cols: int = 3,
) -> str | None:
    width, height = frame_size
    if width <= 0 or height <= 0:
        return None
    if x < 0 or y < 0:
        return None
    cell_w = width / cols
    cell_h = height / rows
    c = min(int(x / cell_w), cols - 1)
    r = min(int(y / cell_h), rows - 1)
    return f"{chr(65 + r)}{c + 1}"
