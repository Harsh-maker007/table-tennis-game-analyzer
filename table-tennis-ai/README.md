# Table Tennis AI Analyzer

Upload a match video and generate basic analysis:

- Ball trajectory tracking
- Shot detection (simple heuristic)
- Player movement coverage
- Table zone heatmap counts
- Strengths and weaknesses by zone

## Structure

```
table-tennis-ai/
  backend/
    main.py
    video_processor.py
    ball_tracking.py
    shot_detection.py
    table_zone_analysis.py
    movement_analysis.py
  models/
    yolov8_table_tennis.pt
  frontend/
    index.html
    dashboard.js
    style.css
  uploads/
  requirements.txt
```

## Setup

1. Place your YOLOv8 model at `models/yolov8_table_tennis.pt`.
   - For a quick demo, this can be a generic `yolov8n.pt` pretrained model.
2. Download MediaPipe Tasks models:
   - `models/mediapipe/pose_landmarker_lite.task`
   - `models/mediapipe/hand_landmarker.task`
2. Install dependencies:
   ```
   pip install -r requirements.txt
   ```
3. Start the backend:
   ```
   uvicorn backend.main:app --reload
   ```
4. Open `frontend/index.html` in a browser.

## Notes

- `shot_detection.py` uses a basic frame-gap heuristic. Replace with a real rally/shot classifier for accuracy.
- If you use a generic COCO model like `yolov8n.pt`, the ball class is `sports ball` (class id 32).
- `table_zone_analysis.py` uses the full frame as the table. Add table detection to map zones only to the table area.
