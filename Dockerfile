FROM python:3.12-slim

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY bithumb_autotrading_v2.py .

VOLUME ["/app/logs"]

CMD ["python", "bithumb_autotrading_v2.py"]
