FROM python:3.12-slim

ENV PYTHONUNBUFFERED=1
ENV PORT=8000

WORKDIR /app

COPY requirements.txt .

RUN pip install --no-cache-dir --upgrade pip \
    && pip install --no-cache-dir -r requirements.txt

COPY app.py .
COPY agents ./agents
COPY workflow ./workflow

CMD ["sh", "-c", "HOST=0.0.0.0 PORT=${PORT} python app.py"]
