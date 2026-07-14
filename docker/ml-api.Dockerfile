FROM python:3.11-slim

WORKDIR /app

# System deps
RUN apt-get update && apt-get install -y --no-install-recommends curl \
    && rm -rf /var/lib/apt/lists/*

# Install Python deps — TF + sklearn + Flask
RUN pip install --no-cache-dir \
    flask==3.1.2 \
    flask-cors==6.0.2 \
    flask-limiter==3.5.0 \
    werkzeug==3.1.3 \
    numpy==1.26.4 \
    pandas==2.2.2 \
    scikit-learn==1.5.0 \
    joblib==1.4.2 \
    tensorflow-cpu==2.16.1 \
    requests==2.32.5

# Copy project files
COPY config.py         /app/config.py
COPY ml_pipeline/      /app/ml_pipeline/
COPY DDoS/             /app/DDoS/

# Copy trained models (mounted as volume in production)
COPY ml_pipeline/models/ /app/ml_pipeline/models/

# Create model directories
RUN mkdir -p /app/models

EXPOSE 5000

# Health check
HEALTHCHECK --interval=30s --timeout=15s --start-period=40s --retries=5 \
    CMD curl -sf http://localhost:5000/api/health || exit 1

CMD ["python", "ml_pipeline/model_api.py"]
