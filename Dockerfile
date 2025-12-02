# Optimized Dockerfile for K8s PVC-based deployment
# Pre-builds PyTorch to eliminate startup downloads
FROM python:3.11-slim

# Set working directory
WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Copy and install only essential Python dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir torch>=2.0 transformers>=4.30 flask>=2.3 datasets>=2.0 scikit-learn>=1.0

# Copy application code (containerized approach)
COPY app.py .
COPY inetuned_gibbrish_detector.py .

# Create non-root user for security
RUN useradd -m -u 1000 appuser && chown -R appuser:appuser /app
USER appuser

# Expose port 8007
EXPOSE 8007

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=60s --retries=3 \
    CMD curl -f http://localhost:8007/health || exit 1

# Environment variables for K8s PVC deployment
ENV MODEL_PATH=/model_volume
ENV FLASK_RUN_PORT=8007

# Run the Flask application (expects model from PVC)
CMD ["python", "app.py"]