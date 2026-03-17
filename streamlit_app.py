import tempfile
from pathlib import Path

import streamlit as st

from table_tennis_entry import analyze_video_file


st.set_page_config(page_title="Table Tennis Game Analyzer", layout="wide")

st.title("Table Tennis Game Analyzer")
st.write("Upload a match video to analyze shots, zones, and movement.")

uploaded = st.file_uploader("Upload match video", type=["mp4", "mov", "avi", "mkv", "webm"])

if uploaded:
    with tempfile.NamedTemporaryFile(delete=False, suffix=Path(uploaded.name).suffix) as tmp:
        tmp.write(uploaded.read())
        tmp_path = tmp.name

    with st.spinner("Analyzing video..."):
        try:
            result = analyze_video_file(tmp_path)
        except Exception as exc:
            st.error(
                "Video analysis failed. This usually happens on Streamlit Cloud "
                "because OpenCV wheels are not available for Python 3.14. "
                "Please redeploy with Python 3.11 or use Docker/Railway."
            )
            st.exception(exc)
            st.stop()

    st.success("Analysis complete.")
    st.subheader("Summary")
    col1, col2, col3 = st.columns(3)
    col1.metric("Total Shots", result.get("total_shots", 0))
    col2.metric("Success Rate", f"{result.get('success_rate', 0):.1f}%")
    col3.metric("Best Zone", result.get("best_zone", "-"))

    st.subheader("Zones")
    st.json(result.get("zones", {}))

    st.subheader("Events")
    st.json(result.get("events", []))
