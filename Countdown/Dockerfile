FROM python:3.11-slim

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

RUN apt-get update && apt-get install -y \
    vi \
    && rm -rf /var/lib/apt/lists/*

COPY . .

EXPOSE 80

# Run gunicorn on port 80
CMD ["gunicorn", "--bind", "0.0.0.0:80", "app:app"]
