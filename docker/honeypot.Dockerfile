FROM python:3.10-slim

# Set work directory
WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Copy requirements
COPY requirements.txt .

# Install Python dependencies
RUN pip install --no-cache-dir flask flask-cors requests pyyaml

# Copy honeypot code
COPY honeypot/ ./honeypot/

# Create logs directory
RUN mkdir -p logs

# Expose honeypot port
EXPOSE 8080

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=20s --retries=3 \
    CMD curl -f http://localhost:8080/health || exit 1

# Set environment variables with defaults
ENV HONEYPOT_TYPE=deceptive
ENV HONEYPOT_SERVICE=ecommerce
ENV ML_API_URL=http://ml-api:5000
ENV PORT=8080

# Run honeypot application
CMD ["python", "honeypot/app.py"]
