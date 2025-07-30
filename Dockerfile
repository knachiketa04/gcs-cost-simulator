# Use Python 3.11 slim image for efficiency
FROM python:3.11-slim

# Set working directory
WORKDIR /app

# Set environment variables
ENV PYTHONUNBUFFERED=1
ENV PYTHONDONTWRITEBYTECODE=1

# Install system dependencies
RUN apt-get update && apt-get install -y \
    gcc \
    && rm -rf /var/lib/apt/lists/*

# Copy requirements first for better caching
COPY requirements.txt .

# Install Python dependencies
RUN pip install --no-cache-dir -r requirements.txt

# Copy application code
COPY gcs-cost-simulator-app/ ./gcs-cost-simulator-app/

# Create a non-root user for security
RUN useradd --create-home --shell /bin/bash app
USER app

# Expose port (Cloud Run will set PORT environment variable)
EXPOSE 8080

# Set default port for Cloud Run
ENV PORT=8080

# Run Streamlit app
CMD streamlit run gcs-cost-simulator-app/app.py \
    --server.port=$PORT \
    --server.address=0.0.0.0 \
    --server.headless=true \
    --server.enableCORS=false \
    --server.enableXsrfProtection=false
