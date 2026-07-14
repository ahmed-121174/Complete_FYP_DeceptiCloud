-- DeceptiCloud Database Schema
-- Central database for all attack events, profiles, and system data

-- Attacks table: All detected attacks
CREATE TABLE IF NOT EXISTS attacks (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    timestamp TEXT NOT NULL,
    ip TEXT NOT NULL,
    user_agent TEXT,
    method TEXT,
    url TEXT,
    path TEXT,
    query_string TEXT,
    attack_type TEXT NOT NULL,
    attack_types_json TEXT,  -- JSON array of all detected attack types
    confidence REAL NOT NULL,
    detection_method TEXT,  -- 'ml', 'rule', 'hybrid'
    routed_to TEXT,  -- 'real' or 'honeypot'
    honeypot_port INTEGER,
    target_site TEXT,
    payload TEXT,
    headers_json TEXT,  -- JSON object of headers
    classification_json TEXT,  -- Full classification result
    captured BOOLEAN DEFAULT 1,
    session_id TEXT,
    created_at TEXT DEFAULT CURRENT_TIMESTAMP
);

-- Attacker profiles table: Fingerprints and behavioral profiles
CREATE TABLE IF NOT EXISTS attacker_profiles (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    ip TEXT NOT NULL UNIQUE,
    first_seen TEXT NOT NULL,
    last_seen TEXT NOT NULL,
    attack_count INTEGER DEFAULT 0,
    attack_types_json TEXT,  -- JSON array of attack types used
    user_agents_json TEXT,  -- JSON array of user agents
    behavioral_hash TEXT,  -- Hash of behavioral patterns
    ja3_fingerprint TEXT,  -- TLS fingerprint
    http_fingerprint TEXT,  -- HTTP header fingerprint
    canvas_fingerprint TEXT,  -- Canvas fingerprint if available
    tools_detected_json TEXT,  -- JSON array of detected tools
    threat_score REAL DEFAULT 0.0,
    cluster_id INTEGER,
    geolocation_json TEXT,  -- JSON object with geo data
    asn TEXT,
    notes TEXT,
    created_at TEXT DEFAULT CURRENT_TIMESTAMP,
    updated_at TEXT DEFAULT CURRENT_TIMESTAMP
);

-- Sessions table: Individual attacker sessions
CREATE TABLE IF NOT EXISTS sessions (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    session_id TEXT NOT NULL UNIQUE,
    ip TEXT NOT NULL,
    profile_id INTEGER,
    start_time TEXT NOT NULL,
    end_time TEXT,
    duration_seconds INTEGER,
    request_count INTEGER DEFAULT 0,
    attack_count INTEGER DEFAULT 0,
    honeypots_visited_json TEXT,  -- JSON array of honeypot names
    actions_json TEXT,  -- JSON array of actions taken
    is_active BOOLEAN DEFAULT 1,
    created_at TEXT DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (profile_id) REFERENCES attacker_profiles(id)
);

-- Events table: System events and logs
CREATE TABLE IF NOT EXISTS events (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    timestamp TEXT NOT NULL,
    event_type TEXT NOT NULL,  -- 'attack', 'system', 'honeypot', 'ml', 'wazuh'
    severity TEXT NOT NULL,  -- 'low', 'medium', 'high', 'critical'
    source TEXT NOT NULL,  -- Component that generated the event
    message TEXT NOT NULL,
    details_json TEXT,  -- JSON object with additional details
    ip TEXT,
    related_attack_id INTEGER,
    created_at TEXT DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (related_attack_id) REFERENCES attacks(id)
);

-- ML Models table: Track model versions and performance
CREATE TABLE IF NOT EXISTS ml_models (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    model_name TEXT NOT NULL,
    model_type TEXT NOT NULL,  -- 'web_attack', 'ddos', 'brute_force', etc.
    version TEXT NOT NULL,
    file_path TEXT NOT NULL,
    accuracy REAL,
    precision_val REAL,
    recall_val REAL,
    f1_score REAL,
    training_date TEXT,
    training_samples INTEGER,
    is_active BOOLEAN DEFAULT 0,
    metadata_json TEXT,  -- JSON object with additional metadata
    created_at TEXT DEFAULT CURRENT_TIMESTAMP,
    UNIQUE(model_name, version)
);

-- Training Data table: Store data for adaptive learning
CREATE TABLE IF NOT EXISTS training_data (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    attack_id INTEGER,
    features_json TEXT NOT NULL,  -- JSON object with feature vector
    label INTEGER NOT NULL,  -- 0 = benign, 1 = attack
    attack_type TEXT,
    confidence REAL,
    verified BOOLEAN DEFAULT 0,  -- Human verified
    used_in_training BOOLEAN DEFAULT 0,
    model_version TEXT,
    created_at TEXT DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (attack_id) REFERENCES attacks(id)
);

-- Wazuh Alerts table: Alerts from Wazuh SIEM
CREATE TABLE IF NOT EXISTS wazuh_alerts (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    timestamp TEXT NOT NULL,
    agent_id TEXT,
    agent_name TEXT,
    rule_id INTEGER,
    rule_level INTEGER,
    rule_description TEXT,
    alert_json TEXT NOT NULL,  -- Full alert JSON
    ip TEXT,
    related_attack_id INTEGER,
    processed BOOLEAN DEFAULT 0,
    created_at TEXT DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (related_attack_id) REFERENCES attacks(id)
);

-- Honeypot Events table: Detailed honeypot interactions
CREATE TABLE IF NOT EXISTS honeypot_events (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    timestamp TEXT NOT NULL,
    honeypot_name TEXT NOT NULL,
    honeypot_port INTEGER NOT NULL,
    event_type TEXT NOT NULL,  -- 'login_attempt', 'form_submit', 'api_call', etc.
    ip TEXT NOT NULL,
    session_id TEXT,
    details_json TEXT,  -- JSON object with event details
    attack_id INTEGER,
    created_at TEXT DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (attack_id) REFERENCES attacks(id)
);

-- Canary Tokens table: Track canary token triggers
CREATE TABLE IF NOT EXISTS canary_tokens (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    token_id TEXT NOT NULL UNIQUE,
    token_type TEXT NOT NULL,  -- 'url', 'email', 'api_key', 'document'
    token_value TEXT NOT NULL,
    honeypot_name TEXT,
    created_at TEXT DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS canary_triggers (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    token_id TEXT NOT NULL,
    timestamp TEXT NOT NULL,
    ip TEXT,
    user_agent TEXT,
    details_json TEXT,
    created_at TEXT DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (token_id) REFERENCES canary_tokens(token_id)
);

-- Routing Rules table: Dynamic routing configuration
CREATE TABLE IF NOT EXISTS routing_rules (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    rule_name TEXT NOT NULL UNIQUE,
    priority INTEGER DEFAULT 0,
    condition_json TEXT NOT NULL,  -- JSON object with matching conditions
    action TEXT NOT NULL,  -- 'route_to_honeypot', 'route_to_real', 'block'
    target_honeypot TEXT,
    is_active BOOLEAN DEFAULT 1,
    created_at TEXT DEFAULT CURRENT_TIMESTAMP,
    updated_at TEXT DEFAULT CURRENT_TIMESTAMP
);

-- System Health table: Track component health over time
CREATE TABLE IF NOT EXISTS system_health (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    timestamp TEXT NOT NULL,
    component_name TEXT NOT NULL,
    component_type TEXT NOT NULL,  -- 'core', 'real', 'honeypot'
    port INTEGER,
    status TEXT NOT NULL,  -- 'UP', 'DOWN', 'DEGRADED'
    response_time_ms INTEGER,
    details_json TEXT,
    created_at TEXT DEFAULT CURRENT_TIMESTAMP
);

-- Indexes for performance
CREATE INDEX IF NOT EXISTS idx_attacks_timestamp ON attacks(timestamp);
CREATE INDEX IF NOT EXISTS idx_attacks_ip ON attacks(ip);
CREATE INDEX IF NOT EXISTS idx_attacks_attack_type ON attacks(attack_type);
CREATE INDEX IF NOT EXISTS idx_attacker_profiles_ip ON attacker_profiles(ip);
CREATE INDEX IF NOT EXISTS idx_sessions_ip ON sessions(ip);
CREATE INDEX IF NOT EXISTS idx_sessions_session_id ON sessions(session_id);
CREATE INDEX IF NOT EXISTS idx_events_timestamp ON events(timestamp);
CREATE INDEX IF NOT EXISTS idx_events_event_type ON events(event_type);
CREATE INDEX IF NOT EXISTS idx_wazuh_alerts_timestamp ON wazuh_alerts(timestamp);
CREATE INDEX IF NOT EXISTS idx_honeypot_events_timestamp ON honeypot_events(timestamp);
CREATE INDEX IF NOT EXISTS idx_honeypot_events_ip ON honeypot_events(ip);
