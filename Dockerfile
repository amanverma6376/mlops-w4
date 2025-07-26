# Use Python 3.10 slim image for better security and smaller size
FROM python:3.10-slim

# Set environment variables
ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PIP_NO_CACHE_DIR=1 \
    PIP_DISABLE_PIP_VERSION_CHECK=1

# Create app directory
WORKDIR /app

# Install minimal system dependencies
RUN apt-get update && apt-get install -y \
    gcc \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Copy minimal requirements for API only
COPY requirements-api.txt .

# Install minimal Python dependencies
RUN pip install --no-cache-dir -r requirements-api.txt

# Copy application code
COPY iris_api.py .
COPY iris_pipeline.py .

# Copy model file if it exists (will be created during CI/CD)
COPY model.pkl* ./

# Create a non-root user for security
RUN adduser --disabled-password --gecos '' --shell /bin/bash user && \
    chown -R user:user /app
USER user

# Expose port
EXPOSE 8000

# Health check
HEALTHCHECK --interval=30s --timeout=30s --start-period=5s --retries=3 \
    CMD curl -f http://localhost:8000/health || exit 1

# Run the application
CMD ["uvicorn", "iris_api:app", "--host", "0.0.0.0", "--port", "8000"] 