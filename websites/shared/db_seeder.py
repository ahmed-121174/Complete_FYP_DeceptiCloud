"""
Database seeder — creates SQLite databases with different data
for real websites vs honeypot clones.
"""

import sqlite3
from pathlib import Path
from datetime import datetime, timedelta
import random
import json
import argparse
import sys

# Phase 2: GAN Data Generator Import

try:
    # Add project root to path

    sys.path.append(str(Path(__file__).parent.parent.parent))
    from honeypot.gan_data_generator import get_gan_factory
    _GAN_AVAILABLE = True
except ImportError:
    _GAN_AVAILABLE = False

SCHEMA = """
CREATE TABLE IF NOT EXISTS users (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    username TEXT NOT NULL,
    password TEXT NOT NULL,
    email TEXT,
    full_name TEXT,
    role TEXT DEFAULT 'user',
    balance REAL DEFAULT 0.0,
    created_at TEXT
);

CREATE TABLE IF NOT EXISTS items (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    name TEXT NOT NULL,
    description TEXT,
    category TEXT,
    price REAL DEFAULT 0.0,
    stock INTEGER DEFAULT 0,
    image_url TEXT,
    created_at TEXT
);

CREATE TABLE IF NOT EXISTS transactions (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id INTEGER,
    item_id INTEGER,
    amount REAL,
    type TEXT,
    status TEXT DEFAULT 'completed',
    reference TEXT,
    created_at TEXT,
    FOREIGN KEY (user_id) REFERENCES users(id)
);

CREATE TABLE IF NOT EXISTS reviews (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    item_id INTEGER,
    author TEXT,
    content TEXT,
    rating INTEGER DEFAULT 5,
    created_at TEXT,
    FOREIGN KEY (item_id) REFERENCES items(id)
);

CREATE TABLE IF NOT EXISTS messages (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    sender TEXT,
    recipient TEXT,
    subject TEXT,
    body TEXT,
    created_at TEXT
);
"""

# SITE-SPECIFIC DATA

SITE_DATA = {
    'banking': {
        'real': {
            'users': [
                ('admin', 'DeceptiCloud', 'admin@securebank.com', 'Sarah Johnson', 'admin', 125000.00),
                ('john.doe', 'p@ssw0rd', 'john@email.com', 'John Doe', 'user', 45230.50),
                ('jane.smith', 'jane123!', 'jane@email.com', 'Jane Smith', 'user', 78900.25),
                ('michael.b', 'mike#456', 'michael@corp.com', 'Michael Brown', 'manager', 92100.00),
                ('alex.w', 'alexPay1', 'alex@mail.com', 'Alex Wilson', 'user', 15400.75),
            ],
            'items': [
                ('Savings Account', 'High-yield savings with 4.5% APY', 'accounts', 0, 999, '/static/images/savings.png'),
                ('Checking Account', 'Zero-fee checking with rewards', 'accounts', 0, 999, '/static/images/checking.png'),
                ('Credit Card Platinum', 'Premium rewards card with 2% cashback', 'cards', 99.99, 500, '/static/images/platinum.png'),
                ('Mortgage Loan', 'Fixed-rate 30-year mortgage at 6.5%', 'loans', 0, 100, '/static/images/mortgage.png'),
                ('Auto Loan', 'New & used car loans from 4.9% APR', 'loans', 0, 200, '/static/images/auto.png'),
                ('Investment Portfolio', 'Managed investment with diversified assets', 'investments', 5000, 50, '/static/images/invest.png'),
            ],
            'transactions': [
                (2, 1, 5000.00, 'deposit', 'completed', 'TXN-2024-001'),
                (3, 3, 250.00, 'payment', 'completed', 'TXN-2024-002'),
                (2, None, 1200.00, 'transfer', 'completed', 'TXN-2024-003'),
                (4, 4, 45000.00, 'loan_payment', 'pending', 'TXN-2024-004'),
                (5, 2, 89.99, 'purchase', 'completed', 'TXN-2024-005'),
            ],
        },
        'honeypot': {
            'users': [
                ('admin', 'DeceptiCloud', 'admin@quickbank.net', 'Robert Taylor', 'admin', 250000.00),
                ('cfo_linda', 'Finance#1', 'linda@quickbank.net', 'Linda Chen', 'admin', 180000.00),
                ('david.k', 'david2024', 'david@email.com', 'David Kim', 'user', 67500.30),
                ('priya.s', 'priya!pass', 'priya@corp.com', 'Priya Singh', 'manager', 110300.00),
                ('omar.h', 'omar1234', 'omar@mail.com', 'Omar Hassan', 'user', 23400.90),
            ],
            'items': [
                ('Premier Savings', 'Premium savings with 5.2% APY', 'accounts', 0, 999, '/static/images/savings.png'),
                ('Business Checking', 'Commercial checking with no min balance', 'accounts', 0, 999, '/static/images/checking.png'),
                ('Gold Credit Card', 'Elite rewards with 3% cashback', 'cards', 149.99, 500, '/static/images/platinum.png'),
                ('Home Equity Loan', 'HELOC at competitive rates', 'loans', 0, 100, '/static/images/mortgage.png'),
                ('Personal Loan', 'Quick personal loans from 5.5%', 'loans', 0, 200, '/static/images/auto.png'),
                ('Retirement Fund', 'IRA with matched contributions', 'investments', 10000, 50, '/static/images/invest.png'),
            ],
            'transactions': [
                (2, 1, 12000.00, 'deposit', 'completed', 'HP-TXN-001'),
                (3, 3, 475.00, 'payment', 'completed', 'HP-TXN-002'),
                (4, None, 8500.00, 'wire_transfer', 'completed', 'HP-TXN-003'),
                (2, 4, 65000.00, 'loan_payment', 'pending', 'HP-TXN-004'),
                (5, 2, 199.99, 'purchase', 'completed', 'HP-TXN-005'),
            ],
        }
    },
    'ecommerce': {
        'real': {
            'users': [
                ('admin', 'DeceptiCloud', 'admin@megastore.com', 'Emily Carter', 'admin', 0),
                ('buyer1', 'buy123!', 'buyer1@email.com', 'Tom Harris', 'user', 450.00),
                ('buyer2', 'shop4Life', 'buyer2@email.com', 'Lisa Wang', 'user', 1200.50),
                ('seller1', 'sell#321', 'seller@market.com', 'Carlos Ruiz', 'seller', 8900.00),
                ('vip_user', 'vipPass1', 'vip@email.com', 'Nina Patel', 'vip', 3400.25),
            ],
            'items': [
                ('Wireless Headphones', 'Noise-cancelling BT headphones with 30hr battery', 'electronics', 159.99, 245, '/static/images/headphones.png'),
                ('Smart Watch Pro', 'Fitness tracking, GPS, heart rate monitor', 'electronics', 299.99, 120, '/static/images/watch.png'),
                ('Organic Coffee Beans', '1kg premium single-origin Arabica beans', 'food', 24.99, 500, '/static/images/coffee.png'),
                ('Running Shoes Ultra', 'Lightweight performance running shoes', 'sports', 129.99, 180, '/static/images/shoes.png'),
                ('Laptop Stand', 'Ergonomic aluminum laptop riser', 'accessories', 49.99, 300, '/static/images/stand.png'),
                ('Mechanical Keyboard', 'RGB backlit with Cherry MX switches', 'electronics', 89.99, 200, '/static/images/keyboard.png'),
            ],
            'transactions': [
                (2, 1, 159.99, 'purchase', 'delivered', 'ORD-2024-1001'),
                (3, 2, 299.99, 'purchase', 'shipped', 'ORD-2024-1002'),
                (5, 3, 49.98, 'purchase', 'delivered', 'ORD-2024-1003'),
                (2, 6, 89.99, 'purchase', 'processing', 'ORD-2024-1004'),
                (3, 4, 129.99, 'refund', 'completed', 'RET-2024-001'),
            ],
        },
        'honeypot': {
            'users': [
                ('admin', 'DeceptiCloud', 'admin@shopnow.io', 'Rachel Green', 'admin', 0),
                ('shopper1', 'shop1pass', 'shop1@email.com', 'James Park', 'user', 670.30),
                ('shopper2', 'buyit456', 'shop2@email.com', 'Aisha Khan', 'user', 2100.00),
                ('vendor1', 'vend#789', 'vendor@biz.com', 'Marco Silva', 'seller', 15600.00),
                ('gold_member', 'goldVIP!', 'gold@email.com', 'Yuki Tanaka', 'vip', 5600.75),
            ],
            'items': [
                ('Bluetooth Speaker', 'Portable waterproof speaker, 20hr battery', 'electronics', 79.99, 310, '/static/images/headphones.png'),
                ('Fitness Tracker', 'Step counter, sleep tracking, notifications', 'electronics', 49.99, 450, '/static/images/watch.png'),
                ('Green Tea Set', 'Traditional ceremony tea set with 6 cups', 'food', 34.99, 200, '/static/images/coffee.png'),
                ('Yoga Mat Premium', 'Non-slip eco-friendly exercise mat', 'sports', 39.99, 280, '/static/images/shoes.png'),
                ('USB-C Hub', '7-in-1 multiport adapter for laptops', 'accessories', 29.99, 400, '/static/images/stand.png'),
                ('Gaming Mouse', 'RGB, 16000 DPI, programmable buttons', 'electronics', 59.99, 175, '/static/images/keyboard.png'),
            ],
            'transactions': [
                (2, 1, 79.99, 'purchase', 'delivered', 'HP-ORD-001'),
                (3, 4, 39.99, 'purchase', 'shipped', 'HP-ORD-002'),
                (4, 6, 59.99, 'purchase', 'delivered', 'HP-ORD-003'),
                (5, 2, 49.99, 'purchase', 'processing', 'HP-ORD-004'),
                (2, 5, 29.99, 'refund', 'completed', 'HP-RET-001'),
            ],
        }
    },
    'healthcare': {
        'real': {
            'users': [
                ('admin', 'DeceptiCloud', 'admin@medclinic.org', 'Dr. Amanda Foster', 'admin', 0),
                ('dr.smith', 'doc#2024', 'smith@medclinic.org', 'Dr. Robert Smith', 'doctor', 0),
                ('nurse.j', 'nurse123', 'jill@medclinic.org', 'Jill Thompson', 'nurse', 0),
                ('patient1', 'pat1pass', 'pat1@email.com', 'William Davis', 'patient', 2500.00),
                ('patient2', 'pat2pass', 'pat2@email.com', 'Maria Garcia', 'patient', 1800.50),
            ],
            'items': [
                ('Annual Checkup', 'Complete physical examination and blood work', 'services', 350.00, 100, '/static/images/checkup.png'),
                ('Dental Cleaning', 'Professional teeth cleaning and exam', 'dental', 200.00, 80, '/static/images/dental.png'),
                ('Eye Examination', 'Comprehensive vision and eye health test', 'vision', 175.00, 60, '/static/images/eye.png'),
                ('Lab Blood Panel', 'Complete blood count and metabolic panel', 'lab', 150.00, 200, '/static/images/lab.png'),
                ('X-Ray Imaging', 'Digital X-ray for bones and joints', 'imaging', 250.00, 50, '/static/images/xray.png'),
                ('Vaccination', 'Flu shot and routine immunizations', 'preventive', 75.00, 500, '/static/images/vaccine.png'),
            ],
            'transactions': [
                (4, 1, 350.00, 'appointment', 'completed', 'APT-2024-001'),
                (5, 2, 200.00, 'appointment', 'completed', 'APT-2024-002'),
                (4, 4, 150.00, 'lab_work', 'pending', 'LAB-2024-001'),
                (5, 6, 75.00, 'vaccination', 'completed', 'VAX-2024-001'),
                (4, 3, 175.00, 'appointment', 'scheduled', 'APT-2024-003'),
            ],
        },
        'honeypot': {
            'users': [
                ('admin', 'DeceptiCloud', 'admin@healthplus.io', 'Dr. Karen White', 'admin', 0),
                ('dr.jones', 'drJones!', 'jones@healthplus.io', 'Dr. Peter Jones', 'doctor', 0),
                ('nurse.m', 'nurseM12', 'mary@healthplus.io', 'Mary Collins', 'nurse', 0),
                ('patient1', 'health1!', 'pt1@email.com', 'Ahmed Hassan', 'patient', 3200.00),
                ('patient2', 'well2024', 'pt2@email.com', 'Sofia Martinez', 'patient', 1500.75),
            ],
            'items': [
                ('Wellness Checkup', 'Full-body health assessment', 'services', 425.00, 100, '/static/images/checkup.png'),
                ('Orthodontic Consult', 'Braces and alignment evaluation', 'dental', 300.00, 60, '/static/images/dental.png'),
                ('Contact Lens Exam', 'Contact fitting and prescription update', 'vision', 195.00, 80, '/static/images/eye.png'),
                ('Allergy Panel', 'Comprehensive allergy testing', 'lab', 275.00, 150, '/static/images/lab.png'),
                ('MRI Scan', 'Magnetic resonance imaging', 'imaging', 800.00, 30, '/static/images/xray.png'),
                ('COVID Booster', 'mRNA booster vaccination', 'preventive', 0.00, 1000, '/static/images/vaccine.png'),
            ],
            'transactions': [
                (4, 1, 425.00, 'appointment', 'completed', 'HP-APT-001'),
                (5, 4, 275.00, 'lab_work', 'completed', 'HP-LAB-001'),
                (4, 5, 800.00, 'imaging', 'pending', 'HP-IMG-001'),
                (5, 6, 0.00, 'vaccination', 'completed', 'HP-VAX-001'),
                (4, 2, 300.00, 'appointment', 'scheduled', 'HP-APT-002'),
            ],
        }
    },
    'blog': {
        'real': {
            'users': [
                ('admin', 'DeceptiCloud', 'admin@techblog.dev', 'Chris Taylor', 'admin', 0),
                ('writer1', 'write#1', 'writer1@blog.com', 'Jessica Lee', 'author', 0),
                ('writer2', 'write#2', 'writer2@blog.com', 'Daniel Baker', 'author', 0),
                ('reader1', 'read1234', 'reader1@email.com', 'Sophie Clark', 'user', 0),
                ('mod_user', 'mod!pass', 'mod@techblog.dev', 'Ryan Moore', 'moderator', 0),
            ],
            'items': [
                ('Getting Started with AI', 'Beginner guide to artificial intelligence concepts', 'tech', 0, 9999, '/static/images/ai.png'),
                ('Cloud Security 101', 'Essential cloud security practices for developers', 'security', 0, 9999, '/static/images/cloud.png'),
                ('Docker for Beginners', 'Complete guide to containerization with Docker', 'devops', 0, 9999, '/static/images/docker.png'),
                ('Python Web Scraping', 'Build web scrapers with Beautiful Soup and Selenium', 'python', 0, 9999, '/static/images/python.png'),
                ('React vs Vue 2024', 'Comparing modern JavaScript frameworks', 'frontend', 0, 9999, '/static/images/react.png'),
                ('SQL Optimization Tips', 'Speed up your database queries by 10x', 'database', 0, 9999, '/static/images/sql.png'),
            ],
            'transactions': [
                (4, 1, 0, 'view', 'completed', 'VIEW-001'),
                (4, 3, 0, 'bookmark', 'completed', 'BM-001'),
                (5, 2, 0, 'share', 'completed', 'SHARE-001'),
                (4, 6, 0, 'view', 'completed', 'VIEW-002'),
                (5, 4, 0, 'comment', 'completed', 'CMT-001'),
            ],
        },
        'honeypot': {
            'users': [
                ('admin', 'DeceptiCloud', 'admin@devnotes.io', 'Kevin Wright', 'admin', 0),
                ('editor1', 'edit#123', 'ed1@devnotes.io', 'Anna Rodriguez', 'author', 0),
                ('editor2', 'edit#456', 'ed2@devnotes.io', 'Mark Thompson', 'author', 0),
                ('subscriber', 'sub1pass', 'sub@email.com', 'Laura Miller', 'user', 0),
                ('moderator', 'modPass!', 'mod@devnotes.io', 'Tyler James', 'moderator', 0),
            ],
            'items': [
                ('Kubernetes Deep Dive', 'Advanced container orchestration techniques', 'devops', 0, 9999, '/static/images/ai.png'),
                ('Ethical Hacking Guide', 'Penetration testing methodology explained', 'security', 0, 9999, '/static/images/cloud.png'),
                ('Microservices Architecture', 'Designing scalable distributed systems', 'architecture', 0, 9999, '/static/images/docker.png'),
                ('Machine Learning Ops', 'MLOps best practices and pipelines', 'ml', 0, 9999, '/static/images/python.png'),
                ('GraphQL vs REST', 'Choosing the right API paradigm', 'api', 0, 9999, '/static/images/react.png'),
                ('NoSQL Database Guide', 'MongoDB, Redis, and Cassandra compared', 'database', 0, 9999, '/static/images/sql.png'),
            ],
            'transactions': [
                (4, 1, 0, 'view', 'completed', 'HP-VIEW-001'),
                (4, 2, 0, 'bookmark', 'completed', 'HP-BM-001'),
                (5, 3, 0, 'share', 'completed', 'HP-SHARE-001'),
                (4, 5, 0, 'view', 'completed', 'HP-VIEW-002'),
                (5, 6, 0, 'comment', 'completed', 'HP-CMT-001'),
            ],
        }
    },
    'api_service': {
        'real': {
            'users': [
                ('admin', 'DeceptiCloud', 'admin@dataapi.io', 'Victoria Chen', 'admin', 0),
                ('dev_user1', 'devKey1!', 'dev1@company.com', 'Nathan Brooks', 'developer', 0),
                ('dev_user2', 'devKey2!', 'dev2@startup.io', 'Zara Ahmed', 'developer', 0),
                ('enterprise', 'entPass!', 'ent@bigcorp.com', 'Global Systems Inc', 'enterprise', 0),
                ('trial_user', 'trial123', 'trial@email.com', 'Sam Peterson', 'trial', 0),
            ],
            'items': [
                ('Basic API Plan', '1000 requests/day, standard support', 'plans', 29.99, 9999, '/static/images/api.png'),
                ('Pro API Plan', '10000 requests/day, priority support', 'plans', 99.99, 9999, '/static/images/api-pro.png'),
                ('Enterprise Plan', 'Unlimited requests, dedicated support', 'plans', 499.99, 9999, '/static/images/enterprise.png'),
                ('Weather API', 'Real-time weather data for 200+ cities', 'endpoints', 0, 9999, '/static/images/weather.png'),
                ('Geocoding API', 'Address to coordinates conversion', 'endpoints', 0, 9999, '/static/images/geo.png'),
                ('Payment Gateway', 'Secure payment processing API', 'endpoints', 0, 9999, '/static/images/payment.png'),
            ],
            'transactions': [
                (2, 1, 29.99, 'subscription', 'active', 'SUB-2024-001'),
                (3, 2, 99.99, 'subscription', 'active', 'SUB-2024-002'),
                (4, 3, 499.99, 'subscription', 'active', 'SUB-2024-003'),
                (2, 4, 0, 'api_call', 'completed', 'API-2024-001'),
                (5, 1, 29.99, 'subscription', 'trial', 'TRIAL-001'),
            ],
        },
        'honeypot': {
            'users': [
                ('admin', 'DeceptiCloud', 'admin@cloudapi.dev', 'Diana Foster', 'admin', 0),
                ('developer1', 'dev1Key!', 'dev1@tech.io', 'Bruce Wayne', 'developer', 0),
                ('developer2', 'dev2Key!', 'dev2@lab.com', 'Clark Kent', 'developer', 0),
                ('business', 'bizPass!', 'biz@enterprise.com', 'Acme Corp', 'enterprise', 0),
                ('free_user', 'free1234', 'free@email.com', 'Peter Parker', 'trial', 0),
            ],
            'items': [
                ('Starter API', '500 requests/day, email support', 'plans', 19.99, 9999, '/static/images/api.png'),
                ('Growth API', '5000 requests/day, chat support', 'plans', 79.99, 9999, '/static/images/api-pro.png'),
                ('Scale API', '50000 requests/day, 24/7 support', 'plans', 299.99, 9999, '/static/images/enterprise.png'),
                ('Translation API', 'Multi-language text translation', 'endpoints', 0, 9999, '/static/images/weather.png'),
                ('Image Recognition', 'AI-powered image analysis', 'endpoints', 0, 9999, '/static/images/geo.png'),
                ('SMS Gateway', 'Global SMS sending API', 'endpoints', 0, 9999, '/static/images/payment.png'),
            ],
            'transactions': [
                (2, 1, 19.99, 'subscription', 'active', 'HP-SUB-001'),
                (3, 2, 79.99, 'subscription', 'active', 'HP-SUB-002'),
                (4, 3, 299.99, 'subscription', 'active', 'HP-SUB-003'),
                (5, 1, 19.99, 'subscription', 'trial', 'HP-TRIAL-001'),
                (2, 4, 0, 'api_call', 'completed', 'HP-API-001'),
            ],
        }
    },
    'corporate': {
        'real': {
            'users': [
                ('admin', 'DeceptiCloud', 'admin@nexagen.com', 'Patricia Clark', 'admin', 0),
                ('hr_manager', 'hr#2024!', 'hr@nexagen.com', 'Jennifer Lewis', 'hr', 0),
                ('employee1', 'emp1pass', 'emp1@nexagen.com', 'Brandon Scott', 'employee', 65000),
                ('employee2', 'emp2pass', 'emp2@nexagen.com', 'Megan Hill', 'employee', 72000),
                ('intern', 'intern24', 'intern@nexagen.com', 'Tyler Ross', 'intern', 25000),
            ],
            'items': [
                ('Cloud Solutions', 'Enterprise cloud migration and management', 'services', 50000, 10, '/static/images/cloud-svc.png'),
                ('Cybersecurity Audit', 'Comprehensive security assessment', 'services', 25000, 20, '/static/images/security.png'),
                ('Data Analytics', 'Business intelligence and data insights', 'services', 35000, 15, '/static/images/analytics.png'),
                ('IT Consulting', 'Strategic technology consulting', 'consulting', 200, 100, '/static/images/consulting.png'),
                ('Training Program', 'Employee skill development workshops', 'training', 5000, 50, '/static/images/training.png'),
                ('Support Contract', '24/7 technical support annual plan', 'support', 12000, 30, '/static/images/support.png'),
            ],
            'transactions': [
                (3, 1, 50000, 'contract', 'active', 'CORP-001'),
                (4, 2, 25000, 'project', 'completed', 'CORP-002'),
                (3, 5, 5000, 'enrollment', 'completed', 'TRAIN-001'),
                (4, 4, 4000, 'consulting', 'in_progress', 'CONSULT-001'),
                (5, 5, 5000, 'enrollment', 'completed', 'TRAIN-002'),
            ],
        },
        'honeypot': {
            'users': [
                ('admin', 'DeceptiCloud', 'admin@quantumtech.io', 'Elizabeth Moore', 'admin', 0),
                ('hr_lead', 'hrLead#1', 'hr@quantumtech.io', 'Christopher Young', 'hr', 0),
                ('staff1', 'staff1pw', 'staff1@quantumtech.io', 'Ashley Turner', 'employee', 70000),
                ('staff2', 'staff2pw', 'staff2@quantumtech.io', 'Jordan Phillips', 'employee', 68000),
                ('contractor', 'contr24!', 'contract@external.com', 'Morgan Bailey', 'contractor', 45000),
            ],
            'items': [
                ('AI Integration', 'Custom AI solutions for enterprise', 'services', 75000, 8, '/static/images/cloud-svc.png'),
                ('Pen Testing', 'Advanced penetration testing service', 'services', 30000, 25, '/static/images/security.png'),
                ('ML Pipeline Setup', 'End-to-end machine learning infrastructure', 'services', 45000, 12, '/static/images/analytics.png'),
                ('DevOps Consulting', 'CI/CD and infrastructure automation', 'consulting', 250, 80, '/static/images/consulting.png'),
                ('Bootcamp Program', 'Intensive developer training bootcamp', 'training', 8000, 40, '/static/images/training.png'),
                ('Premium Support', 'Dedicated team annual support plan', 'support', 18000, 20, '/static/images/support.png'),
            ],
            'transactions': [
                (3, 1, 75000, 'contract', 'active', 'HP-CORP-001'),
                (4, 2, 30000, 'project', 'completed', 'HP-CORP-002'),
                (5, 5, 8000, 'enrollment', 'completed', 'HP-TRAIN-001'),
                (3, 4, 5000, 'consulting', 'in_progress', 'HP-CONSULT-001'),
                (4, 6, 18000, 'support', 'active', 'HP-SUP-001'),
            ],
        }
    },
    'admin_panel': {
        'real': {
            'users': [
                ('superadmin', 'super#123', 'superadmin@sysnet.org', 'James Mitchell', 'superadmin', 0),
                ('admin', 'DeceptiCloud', 'admin@sysnet.org', 'Catherine Brown', 'admin', 0),
                ('dev_ops', 'devOps#1', 'devops@sysnet.org', 'Timothy Lee', 'devops', 0),
                ('analyst', 'anal#321', 'analyst@sysnet.org', 'Rebecca White', 'analyst', 0),
                ('auditor', 'audit!24', 'audit@external.com', 'Frank Green', 'auditor', 0),
            ],
            'items': [
                ('Server Cluster A', 'Primary production servers (8 nodes)', 'infrastructure', 0, 8, '/static/images/server.png'),
                ('Database Cluster', 'PostgreSQL HA cluster (3 nodes)', 'infrastructure', 0, 3, '/static/images/database.png'),
                ('Firewall Rules', 'Active firewall rule configurations', 'security', 0, 150, '/static/images/firewall.png'),
                ('SSL Certificates', 'Managed SSL/TLS certificates', 'security', 0, 25, '/static/images/ssl.png'),
                ('Monitoring Stack', 'Prometheus + Grafana monitoring', 'monitoring', 0, 1, '/static/images/monitor.png'),
                ('Backup System', 'Automated daily backup pipeline', 'backup', 0, 1, '/static/images/backup.png'),
            ],
            'transactions': [
                (3, 1, 0, 'deployment', 'completed', 'DEPLOY-001'),
                (3, 3, 0, 'rule_update', 'completed', 'FW-001'),
                (4, 4, 0, 'cert_renewal', 'pending', 'SSL-001'),
                (2, 2, 0, 'failover_test', 'completed', 'DB-TEST-001'),
                (3, 6, 0, 'backup_run', 'completed', 'BKP-001'),
            ],
        },
        'honeypot': {
            'users': [
                ('root', 'root#pass', 'root@infrahub.net', 'System Root', 'superadmin', 0),
                ('admin', 'DeceptiCloud', 'admin@infrahub.net', 'Sandra Miller', 'admin', 0),
                ('sre_lead', 'sre#2024', 'sre@infrahub.net', 'Patrick Wilson', 'devops', 0),
                ('sec_analyst', 'sec#pass', 'security@infrahub.net', 'Diana Prince', 'analyst', 0),
                ('compliance', 'comp!lia', 'comply@audit.com', 'George Adams', 'auditor', 0),
            ],
            'items': [
                ('Kubernetes Cluster', 'Production K8s cluster (12 pods)', 'infrastructure', 0, 12, '/static/images/server.png'),
                ('Redis Cluster', 'In-memory cache cluster (5 nodes)', 'infrastructure', 0, 5, '/static/images/database.png'),
                ('WAF Rules', 'Web application firewall configs', 'security', 0, 200, '/static/images/firewall.png'),
                ('API Keys', 'Active service API key management', 'security', 0, 40, '/static/images/ssl.png'),
                ('Log Aggregator', 'ELK stack log collection system', 'monitoring', 0, 1, '/static/images/monitor.png'),
                ('DR System', 'Disaster recovery automation', 'backup', 0, 1, '/static/images/backup.png'),
            ],
            'transactions': [
                (3, 1, 0, 'scale_up', 'completed', 'HP-K8S-001'),
                (2, 3, 0, 'rule_update', 'completed', 'HP-WAF-001'),
                (4, 4, 0, 'key_rotation', 'pending', 'HP-KEY-001'),
                (3, 2, 0, 'cache_flush', 'completed', 'HP-REDIS-001'),
                (2, 6, 0, 'dr_test', 'completed', 'HP-DR-001'),
            ],
        }
    },
}

def create_database(db_path, site_type, variant='real'):
    """Create and seed a SQLite database."""
    Path(db_path).parent.mkdir(parents=True, exist_ok=True)

    # Remove existing

    if Path(db_path).exists():
        Path(db_path).unlink()

    conn = sqlite3.connect(db_path)
    conn.executescript(SCHEMA)

    data = SITE_DATA[site_type][variant]
    now = datetime.now().isoformat()

    # Users — apply GAN watermark to honeypot balances so dashboard shows 100% synthetic

    try:
        from config import GAN_WATERMARK_DECIMAL
    except ImportError:
        GAN_WATERMARK_DECIMAL = 7
    for u in data['users']:
        # u = (username, password, email, full_name, role, balance)

        if variant == 'honeypot' and len(u) >= 6:
            u = list(u)
            raw_balance = float(u[5])
            # Embed watermark: drop existing cents, add watermark as last cent digit

            # e.g. 250000.00 → 250000.07, 67500.30 → 67500.07

            watermarked = float(int(raw_balance)) + GAN_WATERMARK_DECIMAL * 0.01
            u[5] = watermarked
        conn.execute(
            'INSERT INTO users (username, password, email, full_name, role, balance, created_at) '
            'VALUES (?, ?, ?, ?, ?, ?, ?)',
            (*u, now)
        )

    # Items

    for it in data['items']:
        conn.execute(
            'INSERT INTO items (name, description, category, price, stock, image_url, created_at) '
            'VALUES (?, ?, ?, ?, ?, ?, ?)',
            (*it, now)
        )

    # Transactions

    for tx in data['transactions']:
        conn.execute(
            'INSERT INTO transactions (user_id, item_id, amount, type, status, reference, created_at) '
            'VALUES (?, ?, ?, ?, ?, ?, ?)',
            (*tx, now)
        )

    # Sample reviews

    conn.execute(
        'INSERT INTO reviews (item_id, author, content, rating, created_at) VALUES '
        '(1, "User123", "Great service, highly recommend!", 5, ?)', (now,)
    )
    conn.execute(
        'INSERT INTO reviews (item_id, author, content, rating, created_at) VALUES '
        '(2, "TestUser", "Good quality, fast delivery.", 4, ?)', (now,)
    )

    conn.commit()
    conn.close()
    print(f"   Created {db_path} ({site_type}/{variant})")

    print(f"   Created {db_path} ({site_type}/{variant})")

def enrich_with_gan(db_path, site_type, seed_data):
    """
    Phase 2: Use WGAN-GP to generate synthetic users and inject into DB.
    Tries to load pre-trained model first; trains from scratch if necessary.
    """
    if not _GAN_AVAILABLE:
        print("    GAN module not available, skipping synthetic data.")
        return

    try:
        from honeypot.gan_data_generator import SyntheticUserFactory
        
        factory = SyntheticUserFactory(model_name=site_type)
        
        # Try to load a pre-trained model first (much faster)

        if factory.load_model():
            print(f"   Loaded pre-trained GAN model for {site_type}")
        else:
            # No pre-trained model — train from scratch (full training)

            print(f"   Training WGAN-GP for {site_type} (2000 epochs)...")
            factory.train(seed_data, epochs=2000, verbose=True)
            factory.save_model()
        
        # Generate 50 synthetic users

        synthetic_users = factory.generate_users(count=50)
        
        conn = sqlite3.connect(db_path)
        now = datetime.now().isoformat()
        
        count = 0
        for u in synthetic_users:
            conn.execute(
                'INSERT INTO users (username, password, email, full_name, role, balance, created_at) '
                'VALUES (?, ?, ?, ?, ?, ?, ?)',
                (u['username'], u['password'], u['email'], u['full_name'], 
                 u['role'], u['balance'], now)
            )
            count += 1
            
        conn.commit()
        conn.close()
        print(f"   Injected {count} GAN-generated users into {db_path}")
        
    except Exception as e:
        print(f"   GAN generation failed: {e}")
        import traceback
        traceback.print_exc()

def seed_all():
    """Create all 14 databases (7 real + 7 honeypot)."""
    parser = argparse.ArgumentParser(description='DeceptiCloud Database Seeder')
    parser.add_argument('--gan', action='store_true', help='Enable GAN synthetic data generation')
    args, _ = parser.parse_known_args()

    db_dir = Path(__file__).parent.parent / 'databases'
    db_dir.mkdir(exist_ok=True)

    print("SEEDING ALL DATABASES")

    for site_type in SITE_DATA:
        for variant in ['real', 'honeypot']:
            db_path = db_dir / f'{site_type}_{variant}.db'
            create_database(str(db_path), site_type, variant)
            
            # (#30) Auto-enrich honeypots with GAN data if pre-trained models exist,

            # or if --gan flag is passed (which triggers training from scratch)

            if variant == 'honeypot':
                model_dir = Path(__file__).parent.parent / 'honeypot' / 'models' / site_type
                if args.gan or (model_dir / 'generator.pt').exists():
                    enrich_with_gan(str(db_path), site_type, SITE_DATA[site_type]['honeypot']['users'])

    print(f"\n Created {len(SITE_DATA) * 2} databases in {db_dir}")

if __name__ == '__main__':
    seed_all()
