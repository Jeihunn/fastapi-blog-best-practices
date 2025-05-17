# Base image
FROM python:3.13-slim

# Prevent Python from buffering stdout/stderr and avoid .pyc files
ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1

# Set working directory
WORKDIR /code

# Install essential system utilities
RUN apt-get update && \
    apt-get install -y --no-install-recommends \
      nano \
      curl && \
    rm -rf /var/lib/apt/lists/*

# Copy and install dependencies
COPY requirements/base.txt requirements/production.txt ./
RUN pip install --no-cache-dir --upgrade pip && \
    pip install --no-cache-dir -r production.txt

# Copy application code
COPY . .

# Expose FastAPI port
EXPOSE 8000

# Run the app
CMD ["gunicorn", "-c", "gunicorn.conf.py", "src.main:app"]
