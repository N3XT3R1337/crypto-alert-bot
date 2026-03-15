FROM python:3.12-slim

WORKDIR /app

RUN apt-get update && \
    apt-get install -y --no-install-recommends gcc && \
    rm -rf /var/lib/apt/lists/*

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY src/ src/

ENV PYTHONPATH=/app/src
ENV PYTHONUNBUFFERED=1

RUN mkdir -p /app/data /app/logs

CMD ["python", "-m", "crypto_alert_bot.bot"]
