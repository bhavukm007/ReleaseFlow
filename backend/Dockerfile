FROM python:3.12-slim
WORKDIR /app
ENV PYTHONDONTWRITEBYTECODE=1 PYTHONUNBUFFERED=1
COPY requirements.txt .
RUN pip install --no-cache-dir --default-timeout=120 --retries=10 -r requirements.txt
COPY . .
EXPOSE 8000
CMD ["sh", "-c", "alembic upgrade head && python seed.py && uvicorn app.main:app --host 0.0.0.0 --port ${PORT:-8000}"]
