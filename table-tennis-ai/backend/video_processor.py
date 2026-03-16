from __future__ import annotations

from pathlib import Path
from typing import Dict, Any

from backend.ball_tracking import track_ball
from backend.movement_analysis import analyze_movement
from backend.shot_detection import detect_shots, calculate_success
from backend.table_zone_analysis import analyze_zones, zone_label


def analyze_video(
    video_path: str | Path,
    model_path: str | Path,
    class_id: int = 0,
    pose_model_path: str | Path | None = None,
    hand_model_path: str | Path | None = None,
) -> Dict[str, Any]:
    ball_positions, frame_size, fps = track_ball(
        video_path, model_path, class_id=class_id
    )
    zones = analyze_zones(ball_positions, frame_size)
    width, height = frame_size
    table_length_m = 2.74
    table_width_m = 1.525
    scale_x = table_length_m / width if width else 0.0
    scale_y = table_width_m / height if height else 0.0
    movement = analyze_movement(
        str(video_path),
        pose_model_path,
        hand_model_path,
        frame_size,
        scale_x,
        scale_y,
        fps,
    )

    shot_indices = detect_shots(ball_positions)
    shots = [{"frame": idx, "result": "unknown"} for idx in shot_indices]
    success_rate = calculate_success(shots)

    width, height = frame_size
    events: list[dict[str, Any]] = []
    gap_threshold = 60
    rallies: list[dict[str, Any]] = []
    shot_type_stats: dict[str, dict[str, Any]] = {}

    def record_shot_stat(shot_type: str, player: str, result: str) -> None:
        if shot_type not in shot_type_stats:
            shot_type_stats[shot_type] = {
                "overall": {"total": 0, "wins": 0, "losses": 0},
                "players": {
                    "A": {"total": 0, "wins": 0, "losses": 0},
                    "B": {"total": 0, "wins": 0, "losses": 0},
                },
            }
        overall = shot_type_stats[shot_type]["overall"]
        player_stats = shot_type_stats[shot_type]["players"][player]
        overall["total"] += 1
        player_stats["total"] += 1
        if result == "win":
            overall["wins"] += 1
            player_stats["wins"] += 1
        elif result == "loss":
            overall["losses"] += 1
            player_stats["losses"] += 1

    def classify_shot(segment: list[dict[str, int]]) -> str:
        if len(segment) < 2 or width == 0 or height == 0:
            return "Rally"
        diag = (width**2 + height**2) ** 0.5
        speeds = []
        ys = []
        xs = []
        for i in range(1, len(segment)):
            x0, y0 = segment[i - 1]["x"], segment[i - 1]["y"]
            x1, y1 = segment[i]["x"], segment[i]["y"]
            dx = x1 - x0
            dy = y1 - y0
            dist = (dx * dx + dy * dy) ** 0.5
            speeds.append(dist / diag)
            ys.append(y1)
            xs.append(x1)
        avg_speed = sum(speeds) / len(speeds)
        arc = (max(ys) - min(ys)) / height if height else 0.0
        lateral = (max(xs) - min(xs)) / width if width else 0.0

        if avg_speed >= 0.06 and arc <= 0.12:
            return "Smash"
        if arc >= 0.35 and avg_speed <= 0.03:
            return "Lob"
        if avg_speed <= 0.008:
            return "Drop shot"
        if avg_speed <= 0.02 and arc <= 0.12:
            return "Push"
        if lateral >= 0.25 and arc >= 0.18:
            return "Hook"
        if arc >= 0.25 and avg_speed >= 0.025:
            return "Loop drive"
        if avg_speed >= 0.04 and arc <= 0.2:
            return "Counterdrive"
        if avg_speed >= 0.025 and arc <= 0.2:
            return "Flick/flip"
        if avg_speed <= 0.02 and arc <= 0.2:
            return "Chop"
        return "Block"

    if ball_positions:
        segments: list[list[dict[str, int]]] = []
        current: list[dict[str, int]] = []
        last_frame = ball_positions[0]["frame"]
        for item in ball_positions:
            frame = int(item.get("frame", 0))
            if frame - last_frame > gap_threshold and current:
                segments.append(current)
                current = []
            current.append(item)
            last_frame = frame
        if current:
            segments.append(current)

        for seg in segments:
            shot_type = classify_shot(seg)
            start_frame = int(seg[0].get("frame", 0))
            end_frame = int(seg[-1].get("frame", 0))
            duration = max(1, end_frame - start_frame)
            diag = (width**2 + height**2) ** 0.5 if width and height else 1.0
            rally_speeds = []
            for i in range(1, len(seg)):
                dx = seg[i]["x"] - seg[i - 1]["x"]
                dy = seg[i]["y"] - seg[i - 1]["y"]
                dist_m = (
                    ((dx * scale_x) ** 2 + (dy * scale_y) ** 2) ** 0.5
                    if scale_x and scale_y
                    else 0.0
                )
                rally_speeds.append(dist_m)
            avg_speed_mps = (
                (sum(rally_speeds) / len(rally_speeds)) * fps
                if rally_speeds
                else 0.0
            )
            avg_speed_kmh = avg_speed_mps * 3.6

            for item in seg[:-1]:
                x = int(item.get("x", 0))
                y = int(item.get("y", 0))
                player = "A" if x < width / 2 else "B"
                events.append(
                    {
                        "x": x / width if width else 0.0,
                        "y": y / height if height else 0.0,
                        "zone": zone_label(x, y, frame_size),
                        "player": player,
                        "result": "rally",
                        "frame": int(item.get("frame", 0)),
                    }
                )

            last = seg[-1]
            x = int(last.get("x", 0))
            y = int(last.get("y", 0))
            player = "A" if x < width / 2 else "B"
            net_band = (height * 0.48, height * 0.52)
            is_net = net_band[0] <= y <= net_band[1]
            zone = "NET" if is_net else zone_label(x, y, frame_size)
            win_event = {
                "x": x / width if width else 0.0,
                "y": y / height if height else 0.0,
                "zone": zone,
                "player": player,
                "result": "win",
                "frame": int(last.get("frame", 0)),
                "shot_type": shot_type,
            }
            loss_event = {
                "x": x / width if width else 0.0,
                "y": y / height if height else 0.0,
                "zone": zone,
                "player": "B" if player == "A" else "A",
                "result": "loss",
                "frame": int(last.get("frame", 0)),
                "shot_type": shot_type,
            }
            events.append(
                {
                    **win_event,
                }
            )
            events.append(
                {
                    **loss_event,
                }
            )

            record_shot_stat(shot_type, player, "win")
            record_shot_stat(shot_type, "B" if player == "A" else "A", "loss")
            rallies.append(
                {
                    "start_frame": start_frame,
                    "end_frame": end_frame,
                    "duration_frames": duration,
                    "avg_speed_kmh": avg_speed_kmh,
                    "shot_type": shot_type,
                    "winner": player,
                }
            )

    best_zone = max(zones, key=zones.get) if zones else None
    weak_zone = min(zones, key=zones.get) if zones else None

    return {
        "total_shots": len(shot_indices),
        "success_rate": success_rate,
        "zones": zones,
        "best_zone": best_zone,
        "weak_zone": weak_zone,
        "movement": movement,
        "events": events,
        "rallies": rallies,
        "shot_type_stats": shot_type_stats,
        "speed_units": "km/h",
    }
