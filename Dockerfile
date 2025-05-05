FROM python:3.11-slim

RUN apt update && \
    apt install -y curl libpq-dev && \
    apt clean && \
    rm -rf /var/lib/apt/lists/*

COPY requirements.txt /app/requirements.txt
RUN pip install --no-cache-dir -r /app/requirements.txt

COPY ./app /app

CMD ["uvicorn", "app.api:app", "--host", "0.0.0.0", "--port", "8080"]
