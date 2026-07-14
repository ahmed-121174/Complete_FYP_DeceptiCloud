"""
Shared website factory for creating real and honeypot website instances.
Each site has the same UI but connects to different databases.
"""

import os
import sqlite3
import json
from pathlib import Path
from datetime import datetime, timedelta
from flask import Flask, render_template, request, jsonify, redirect, url_for, session
import logging
import random
import string

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

import sys
# Add project root to sys.path for database and honeypot access
_project_root = str(Path(__file__).parent.parent.parent.resolve())
if _project_root not in sys.path:
    sys.path.insert(0, _project_root)

try:
    from honeypot.logger import HoneypotLogger
    _LOGGER_AVAILABLE = True
except ImportError:
    _LOGGER_AVAILABLE = False

def create_app(site_config):
    """
    Factory function to create a Flask app for any site type.

    site_config = {
        'name': 'SecureBank',
        'type': 'banking',       # banking|ecommerce|healthcare|blog|api|corporate|admin
        'is_honeypot': False,
        'db_path': 'banking_real.db',  # SQLite path
        'port': 3001,
        'theme_color': '#1a5276',
        'tagline': 'Your Trusted Financial Partner',
    }
    """
    template_dir = Path(__file__).parent.parent / 'templates'
    static_dir = Path(__file__).parent.parent / 'static'

    app = Flask(__name__,
                template_folder=str(template_dir),
                static_folder=str(static_dir))
    app.secret_key = os.urandom(24)
    app.config['SITE'] = site_config
    app.config['DB_PATH'] = site_config['db_path']

    def get_db():
        """Get SQLite connection."""
        db = sqlite3.connect(app.config['DB_PATH'])
        db.row_factory = sqlite3.Row
        return db

    # Initialize centralized logger
    if _LOGGER_AVAILABLE:
        hp_logger = HoneypotLogger(
            honeypot_type='deceptive',
            service=site_config['type']
        )
    else:
        hp_logger = None

    def log_event(event_type, data):
        """Log honeypot events to both file and central database."""
        if hp_logger:
            hp_logger.log_interaction({
                'action': event_type,
                'ip': data.get('ip', request.remote_addr),
                **data
            })
        else:
            # Fallback to local file if centralized logger not available
            log_dir = Path('logs')
            log_dir.mkdir(exist_ok=True)
            entry = {
                'timestamp': datetime.now().isoformat(),
                'event': event_type,
                'data': data
            }
            with open(log_dir / 'honeypot_events.jsonl', 'a') as f:
                f.write(json.dumps(entry) + '\n')

    # ROUTES

    @app.route('/')
    def index():
        db = get_db()
        try:
            items = db.execute(
                'SELECT * FROM items ORDER BY id DESC LIMIT 6'
            ).fetchall()
        except:
            items = []
        db.close()
        return render_template('index.html', site=site_config, items=items)

    @app.route('/login', methods=['GET', 'POST'])
    def login():
        error = None
        if request.method == 'POST':
            username = request.form.get('username', '')
            password = request.form.get('password', '')

            # Log attempt (honeypot captures credentials)

            if site_config['is_honeypot']:
                log_event('login_attempt', {
                    'username': username,
                    'password': password,
                    'ip': request.remote_addr
                })

            db = get_db()
            user = db.execute(
                'SELECT * FROM users WHERE username = ? AND password = ?',
                (username, password)
            ).fetchone()
            db.close()

            if user:
                session['user'] = username
                session['role'] = user['role']
                return redirect(url_for('dashboard'))
            else:
                error = 'Invalid credentials. Please try again.'

        return render_template('login.html', site=site_config, error=error)

    @app.route('/register', methods=['GET', 'POST'])
    def register():
        message = None
        if request.method == 'POST':
            if site_config['is_honeypot']:
                log_event('registration_attempt', {
                    'data': dict(request.form),
                    'ip': request.remote_addr
                })
            message = 'Registration successful! Please login.'
        return render_template('register.html', site=site_config, message=message)

    @app.route('/dashboard')
    def dashboard():
        if 'user' not in session:
            return redirect(url_for('login'))
        db = get_db()
        try:
            stats = {
                'users': db.execute('SELECT COUNT(*) FROM users').fetchone()[0],
                'items': db.execute('SELECT COUNT(*) FROM items').fetchone()[0],
                'transactions': db.execute('SELECT COUNT(*) FROM transactions').fetchone()[0],
            }
        except:
            stats = {'users': 0, 'items': 0, 'transactions': 0}
        db.close()
        return render_template('dashboard.html', site=site_config, stats=stats,
                               user=session.get('user'))

    @app.route('/search')
    def search():
        query = request.args.get('q', '')
        results = []
        if query:
            if site_config['is_honeypot']:
                log_event('search_query', {
                    'query': query,
                    'ip': request.remote_addr
                })
            db = get_db()
            try:
                # Intentionally vulnerable to SQLi for honeypot demonstration

                results = db.execute(
                    f"SELECT * FROM items WHERE name LIKE '%{query}%' OR description LIKE '%{query}%'"
                ).fetchall()
            except Exception as e:
                if site_config['is_honeypot']:
                    log_event('sqli_detected', {
                        'query': query,
                        'error': str(e),
                        'ip': request.remote_addr
                    })
                results = []
            db.close()
        return render_template('search.html', site=site_config,
                               query=query, results=results)

    @app.route('/items')
    def items_list():
        db = get_db()
        items = db.execute('SELECT * FROM items ORDER BY id').fetchall()
        db.close()
        return render_template('items.html', site=site_config, items=items)

    @app.route('/item/<int:item_id>')
    def item_detail(item_id):
        db = get_db()
        item = db.execute('SELECT * FROM items WHERE id = ?', (item_id,)).fetchone()
        reviews = db.execute(
            'SELECT * FROM reviews WHERE item_id = ? ORDER BY id DESC', (item_id,)
        ).fetchall()
        db.close()
        if not item:
            return render_template('404.html', site=site_config), 404
        return render_template('item_detail.html', site=site_config,
                               item=item, reviews=reviews)

    @app.route('/review', methods=['POST'])
    def submit_review():
        """XSS target — accepts user content."""
        item_id = request.form.get('item_id', 1)
        content = request.form.get('content', '')
        author = request.form.get('author', 'Anonymous')

        if site_config['is_honeypot']:
            log_event('review_submission', {
                'content': content,
                'author': author,
                'ip': request.remote_addr
            })

        db = get_db()
        db.execute(
            'INSERT INTO reviews (item_id, author, content, created_at) VALUES (?, ?, ?, ?)',
            (item_id, author, content, datetime.now().isoformat())
        )
        db.commit()
        db.close()
        return redirect(url_for('item_detail', item_id=item_id))

    @app.route('/api/data')
    def api_data():
        """API endpoint — target for injection."""
        category = request.args.get('category', '')
        db = get_db()
        if category:
            items = db.execute(
                f"SELECT * FROM items WHERE category = '{category}'"
            ).fetchall()
        else:
            items = db.execute('SELECT * FROM items').fetchall()
        db.close()
        return jsonify([dict(row) for row in items])

    @app.route('/api/users')
    def api_users():
        """API endpoint for user data."""
        db = get_db()
        users = db.execute(
            'SELECT id, username, email, role FROM users'
        ).fetchall()
        db.close()
        return jsonify([dict(row) for row in users])

    @app.route('/admin')
    def admin():
        if session.get('role') != 'admin':
            if site_config['is_honeypot']:
                log_event('admin_access_attempt', {'ip': request.remote_addr})
            return render_template('login.html', site=site_config,
                                   error='Admin access required')
        db = get_db()
        users = db.execute('SELECT * FROM users').fetchall()
        transactions = db.execute(
            'SELECT * FROM transactions ORDER BY id DESC LIMIT 20'
        ).fetchall()
        db.close()
        return render_template('admin.html', site=site_config,
                               users=users, transactions=transactions)

    @app.route('/profile')
    def profile():
        if 'user' not in session:
            return redirect(url_for('login'))
        db = get_db()
        user = db.execute(
            'SELECT * FROM users WHERE username = ?', (session['user'],)
        ).fetchone()
        db.close()
        return render_template('profile.html', site=site_config, user=user)

    @app.route('/logout')
    def logout():
        session.clear()
        return redirect(url_for('index'))

    @app.route('/health')
    def health():
        return jsonify({
            'status': 'healthy',
            'site': site_config['name'],
            'type': site_config['type'],
            'is_honeypot': site_config['is_honeypot'],
            'timestamp': datetime.now().isoformat()
        })

    @app.errorhandler(404)
    def not_found(e):
        return render_template('404.html', site=site_config), 404

    # PHASE 1 EXTENSIONS — Honeypot-only features

    if site_config.get('is_honeypot', False):
        try:
            import sys
            # Add project root to path for imports

            project_root = str(Path(__file__).parent.parent.parent)
            if project_root not in sys.path:
                sys.path.insert(0, project_root)

            # Register Canary Tokens (trap routes)

            from honeypot.canary_tokens import canary_bp
            app.register_blueprint(canary_bp)
            logger.info(f" Canary Tokens enabled for {site_config['name']}")

            # Register Behavioral Fingerprinting

            from honeypot.behavioral_fingerprint import fingerprint_bp
            app.register_blueprint(fingerprint_bp)
            logger.info(f" Behavioral Fingerprinting enabled for {site_config['name']}")
        except ImportError as e:
            logger.warning(f"Phase 1 extensions not loaded: {e}")

    return app

