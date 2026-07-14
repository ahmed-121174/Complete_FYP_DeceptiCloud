FROM python:3.11-slim

WORKDIR /app

# System deps
RUN apt-get update && apt-get install -y --no-install-recommends curl \
    && rm -rf /var/lib/apt/lists/*

# Install Python deps
RUN pip install --no-cache-dir \
    flask==3.1.2 \
    flask-cors==6.0.2 \
    flask-limiter==3.5.0 \
    werkzeug==3.1.3 \
    requests==2.32.5

# Copy project files
COPY config.py         /app/config.py
COPY dashboard/        /app/dashboard/

# Create log directories
RUN mkdir -p /app/logs /app/proxy/logs

EXPOSE 9000

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=15s --retries=3 \
    CMD curl -sf http://localhost:9000/ || exit 1

CMD ["python", "dashboard/app.py"]
