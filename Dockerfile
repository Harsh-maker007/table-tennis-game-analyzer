FROM python:3.11-slim

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1

WORKDIR /app

COPY table-tennis-ai/requirements.txt /app/requirements.txt
RUN pip install --no-cache-dir -r requirements.txt

COPY table-tennis-ai /app
COPY streamlit_app.py /app/streamlit_app.py
COPY table_tennis_entry.py /app/table_tennis_entry.py

EXPOSE 8000

CMD ["uvicorn", "backend.main:app", "--host", "0.0.0.0", "--port", "8000"]
