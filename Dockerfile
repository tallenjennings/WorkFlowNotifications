FROM python:3.12-slim

WORKDIR /app

COPY . /app

RUN pip install --no-cache-dir .

CMD ["bash", "-lc", "alembic upgrade head && python scripts/seed.py && uvicorn app.main:app --host 0.0.0.0 --port 8000"]