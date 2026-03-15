FROM python:3.11-slim

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

RUN mkdir -p /data/storage /data && \
    chown -R 1000:1000 /data

USER 1000

EXPOSE 5051

CMD ["gunicorn", "--bind", "0.0.0.0:5051", "--workers", "4", "--timeout", "120", "--access-logfile", "-", "--error-logfile", "-", "app:app"]
