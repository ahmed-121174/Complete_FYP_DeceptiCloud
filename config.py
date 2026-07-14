import os

# SERVICE PORTS

ML_API_PORT = int(os.environ.get('ML_API_PORT', 5000))
PROXY_PORT = int(os.environ.get('PROXY_PORT', 8080))
DASHBOARD_PORT = int(os.environ.get('DASHBOARD_PORT', 9000))

# Real website ports: 3001-3007

REAL_SITE_BASE_PORT = int(os.environ.get('REAL_SITE_BASE_PORT', 3001))
# Honeypot website ports: 4001-4007

HONEYPOT_SITE_BASE_PORT = int(os.environ.get('HONEYPOT_SITE_BASE_PORT', 4001))

# SERVICE URLS (derived from ports)

ML_API_URL = os.environ.get('ML_API_URL', f'http://localhost:{ML_API_PORT}')
PROXY_URL = os.environ.get('PROXY_URL', f'http://localhost:{PROXY_PORT}')
DASHBOARD_URL = os.environ.get('DASHBOARD_URL', f'http://localhost:{DASHBOARD_PORT}')

# HONEYPOT PORT LIST

SITE_TYPES = ['banking', 'ecommerce', 'healthcare', 'blog', 'api_service', 'corporate', 'admin_panel']
HONEYPOT_PORTS = [HONEYPOT_SITE_BASE_PORT + i for i in range(len(SITE_TYPES))]

# AUTHENTICATION

# Dashboard default credentials

DASHBOARD_DEFAULT_USERNAME = os.environ.get('DASHBOARD_USERNAME', 'admin')
DASHBOARD_DEFAULT_PASSWORD = os.environ.get('DASHBOARD_PASSWORD', 'DeceptiCloud')

# Dashboard session persistence

DASHBOARD_SECRET_KEY = os.environ.get('DASHBOARD_SECRET', 'decepticloud-session-key-change-in-prod')

# Proxy API key (for internal config endpoints)

PROXY_API_KEY = os.environ.get('PROXY_API_KEY', 'decepti-internal-api-key')

# PROXY SETTINGS

DEFAULT_SITE = os.environ.get('DEFAULT_SITE', 'banking')
ROTATION_INTERVAL = int(os.environ.get('ROTATION_INTERVAL', 60))

# Detection thresholds (calibrated values)

RULE_SCORE_HIGH_THRESHOLD = float(os.environ.get('RULE_SCORE_HIGH', 0.5))
RULE_SCORE_LOW_THRESHOLD = float(os.environ.get('RULE_SCORE_LOW', 0.3))
ML_CONFIDENCE_THRESHOLD = float(os.environ.get('ML_CONFIDENCE', 0.7))

# RATE LIMITING

RATE_LIMIT_DEFAULT = os.environ.get('RATE_LIMIT_DEFAULT', '200/minute')
RATE_LIMIT_LOGIN = os.environ.get('RATE_LIMIT_LOGIN', '5/minute')
RATE_LIMIT_ML_API = os.environ.get('RATE_LIMIT_ML_API', '100/minute')

# ML API SETTINGS

MAX_FEATURE_COUNT = int(os.environ.get('MAX_FEATURE_COUNT', 100))

# Feature order for the web attack model — shared between proxy and ML API

FEATURE_ORDER = [
    'url_length', 'path_length', 'query_length', 'fragment_length',
    'num_params', 'param_value_length', 'has_ip_address', 'num_special_chars',
    'has_encoded_chars', 'num_path_segments', 'has_file_extension',
    'content_length', 'num_headers', 'has_cookie', 'has_auth_header',
    'has_user_agent', 'is_post', 'is_put', 'is_delete',
    'sqli_score', 'xss_score', 'traversal_score',
]

# GAN SETTINGS

GAN_WATERMARK_DECIMAL = int(os.environ.get('GAN_WATERMARK_DECIMAL', 7))
GAN_WATERMARK_RATIO = float(os.environ.get('GAN_WATERMARK_RATIO', 0.3)) 
GAN_DEFAULT_EPOCHS = int(os.environ.get('GAN_EPOCHS', 2000))
GAN_MODE_COLLAPSE_CHECK_INTERVAL = 200
GAN_MODE_COLLAPSE_STD_THRESHOLD = 0.01
