# Stage 1: Build
FROM python:3.12-slim as builder

WORKDIR /app

ENV PYTHONDONTWRITEBYTECODE 1
ENV PYTHONUNBUFFERED 1

RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    libpq-dev \
    && rm -rf /var/lib/apt/lists/*

COPY requirements.txt .
RUN pip install --no-cache-dir --upgrade pip \
    && pip install --no-cache-dir --prefix=/install -r requirements.txt

# Stage 2: Runtime
FROM python:3.12-slim

WORKDIR /app

# Copy installed dependencies from builder
COPY --from=builder /install /usr/local
COPY . .

# Security: Run as non-root user
RUN adduser --disabled-password --gecos "" orbidiuser
USER orbidiuser

EXPOSE 8000

# High-performance execution with 4 workers to handle concurrency
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000", "--workers", "4"]