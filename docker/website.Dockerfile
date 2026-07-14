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

# Copy project code
COPY config.py             /app/config.py
COPY websites/             /app/websites/
COPY honeypot/canary_tokens.py     /app/honeypot/canary_tokens.py
COPY honeypot/behavioral_fingerprint.py /app/honeypot/behavioral_fingerprint.py
COPY honeypot/__init__.py          /app/honeypot/__init__.py

# Create required directories
RUN mkdir -p /app/websites/databases /app/logs

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=15s --retries=3 \
    CMD curl -sf "http://localhost:${SITE_PORT:-3001}/" > /dev/null || exit 1

# Entrypoint script baked in
CMD python -c "\
    import os, sys; \
    sys.path.insert(0, '/app'); \
    sys.path.insert(0, '/app/websites'); \
    from websites.shared.db_seeder import create_database; \
    from websites.shared.site_factory import create_app; \
    site_type = os.environ['SITE_TYPE']; \
    variant    = os.environ.get('SITE_VARIANT', 'real'); \
    port       = int(os.environ.get('SITE_PORT', '3001')); \
    db_path    = f'/app/websites/databases/{site_type}_{variant}.db'; \
    create_database(db_path, site_type, variant); \
    config = { \
    'name':        os.environ.get('SITE_NAME', site_type), \
    'type':        site_type, \
    'is_honeypot': os.environ.get('IS_HONEYPOT', 'false').lower() == 'true', \
    'db_path':     db_path, \
    'port':        port, \
    'theme_color': os.environ.get('THEME_COLOR', '#1a5276'), \
    'tagline':     os.environ.get('TAGLINE', 'Welcome'), \
    'icon':        'pot' if os.environ.get('IS_HONEYPOT', 'false').lower() == 'true' else ' lock', \
    'items_label': 'Items', \
    }; \
    app = create_app(config); \
    app.run(host='0.0.0.0', port=port)"
