
// Chart.js defaults

Chart.defaults.color = '#475569';
Chart.defaults.borderColor = 'rgba(59,130,246,0.08)';
Chart.defaults.font.family = "'Inter', sans-serif";

const COLORS = ['#ff3366', '#ffaa00', '#a855f7', '#00f0ff', '#00ff88', '#ff6b2b', '#ec4899', '#3b82f6'];
const BADGE_MAP = {
    'sqli': 'badge-sqli', 'xss': 'badge-xss', 'nosqli': 'badge-nosqli',
    'sql injection': 'badge-sqli', 'path traversal': 'badge-traversal',
    'traversal': 'badge-traversal', 'suspicious tool': 'badge-tool',
    'brute force': 'badge-sqli', 'ddos': 'badge-xss', 'port scan': 'badge-traversal',
    'credential stuffing': 'badge-nosqli', 'web attack': 'badge-tool',
    'command injection': 'badge-sqli',
};

// ── Toast notification (replaces all alert() popups) ─────────────────────────
function showToast(message, type = 'info', duration = 4000) {
    let container = document.getElementById('toast-container');
    if (!container) {
        container = document.createElement('div');
        container.id = 'toast-container';
        container.style.cssText = [
            'position:fixed', 'bottom:24px', 'right:24px', 'z-index:99999',
            'display:flex', 'flex-direction:column', 'gap:8px', 'pointer-events:none'
        ].join(';');
        document.body.appendChild(container);
    }
    const colors = { success: '#00ff88', error: '#ff3366', info: '#00f0ff', warning: '#ffaa00' };
    const icons = { success: '✓', error: '✗', info: 'ℹ', warning: '⚠' };
    const color = colors[type] || colors.info;
    const icon = icons[type] || icons.info;
    const toast = document.createElement('div');
    toast.style.cssText = [
        `background:rgba(10,17,40,0.97)`, `border:1px solid ${color}40`,
        `border-left:3px solid ${color}`, 'border-radius:8px',
        'padding:12px 16px', 'min-width:260px', 'max-width:420px',
        'font-size:0.82rem', 'color:#e2e8f0', 'pointer-events:all',
        'box-shadow:0 8px 24px rgba(0,0,0,0.5)',
        'animation:slideInToast 0.25s ease', 'white-space:pre-wrap', 'line-height:1.5'
    ].join(';');
    toast.innerHTML = `<span style="color:${color};font-weight:700;margin-right:6px">${icon}</span>${message}`;
    container.appendChild(toast);
    if (!document.getElementById('toast-keyframes')) {
        const s = document.createElement('style');
        s.id = 'toast-keyframes';
        s.textContent = '@keyframes slideInToast{from{opacity:0;transform:translateX(40px)}to{opacity:1;transform:translateX(0)}}';
        document.head.appendChild(s);
    }
    setTimeout(() => { toast.style.opacity = '0'; toast.style.transition = 'opacity 0.3s'; setTimeout(() => toast.remove(), 300); }, duration);
}

// ── HTML escape (prevents XSS from attack payloads stored in DB) ────────────
function escapeHtml(s) {
    return String(s === null || s === undefined ? '' : s)
        .replace(/&/g, '&amp;')
        .replace(/</g, '&lt;')
        .replace(/>/g, '&gt;')
        .replace(/"/g, '&quot;')
        .replace(/'/g, '&#39;');
}


let currentPage = 'overview';
let charts = {};
let refreshTimers = [];
let attackCount = 0;

// AUTH

async function doLogin() {
    const user = document.getElementById('login-user').value;
    const pass = document.getElementById('login-pass').value;
    const btn = document.getElementById('login-btn');
    const err = document.getElementById('login-error');
    err.textContent = '';
    btn.classList.add('loading');
    btn.textContent = 'AUTHENTICATING...';
    try {
        const r = await fetch('/api/login', {
            method: 'POST', headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ username: user, password: pass })
        });
        const d = await r.json();
        if (d.status === 'success') {
            document.getElementById('login-screen').classList.add('hidden');
            document.querySelector('.app-shell').classList.add('active');
            document.getElementById('user-name').textContent = d.user.name;
            document.getElementById('user-role').textContent = d.user.role;
            document.getElementById('sidebar-uname').textContent = d.user.name;
            document.getElementById('sidebar-urole').textContent = d.user.role;
            initDashboard();
        } else {
            err.textContent = d.message || 'Invalid credentials';
        }
    } catch (e) {
        err.textContent = 'Connection error — is the server running?';
    }
    btn.classList.remove('loading');
    btn.textContent = 'ACCESS SYSTEM';
}

async function doLogout() {
    await fetch('/api/logout', { method: 'POST' }).catch(() => { });
    location.reload();
}

async function checkSession() {
    try {
        const r = await fetch('/api/me');
        if (r.ok) {
            const d = await r.json();
            if (d.authenticated) {
                document.getElementById('login-screen').classList.add('hidden');
                document.querySelector('.app-shell').classList.add('active');
                document.getElementById('user-name').textContent = d.name;
                document.getElementById('user-role').textContent = d.role;
                document.getElementById('sidebar-uname').textContent = d.name;
                document.getElementById('sidebar-urole').textContent = d.role;
                initDashboard();
                return;
            }
        }
    } catch (e) { }
    document.getElementById('login-screen').classList.remove('hidden');
}

// NAVIGATION

function navigateTo(page) {
    currentPage = page;
    document.querySelectorAll('.page-view').forEach(p => p.classList.remove('active'));
    document.querySelectorAll('.nav-item').forEach(n => n.classList.remove('active'));
    const target = document.getElementById('page-' + page);
    const nav = document.querySelector(`.nav-item[data-page="${page}"]`);
    if (target) target.classList.add('active');
    if (nav) nav.classList.add('active');
    // Update topbar title

    const titles = {
        overview: 'Command Overview', attacks: 'Attack Analysis', honeypots: 'Honeypot Management',
        models: 'ML Detection Models', adaptive: 'Adaptive Learning Engine', sitelogs: 'Site Logs & Telemetry',
        blockchain: 'Blockchain Ledger', canary: 'Canary Tokens',
        fingerprints: 'Behavioral Fingerprints', settings: 'System Settings'
    };
    document.getElementById('topbar-title').textContent = titles[page] || 'Dashboard';
    // Load page data

    loadPageData(page);

    // Reinitialize icons after page change
    setTimeout(() => {
        if (typeof window.initializeIcons === 'function') {
            window.initializeIcons();
        }
    }, 100);
}

function toggleSidebar() {
    document.querySelector('.sidebar').classList.toggle('collapsed');
}

// INIT

function initDashboard() {
    initCharts();
    loadPageData('overview');
    // Global refresh every 5s

    refreshTimers.push(setInterval(() => loadPageData(currentPage), 5000));
    // Health-only fast refresh every 2s — updates 16/16 counter and dots in near real time

    refreshTimers.push(setInterval(async () => {
        try {
            const health = await fetch('/api/system-health').then(r => r.json()).catch(() => ({}));
            const services = health.services || {};
            const filteredServices = Object.fromEntries(Object.entries(services).filter(([name]) => name !== 'SSH Honeypot'));
            const hc = Object.values(filteredServices).filter(s => s.status === 'healthy').length;
            const tc = Object.keys(filteredServices).length;

            if (tc > 0) {
                document.getElementById('stat-health').textContent = `${hc}/${tc}`;
                document.getElementById('stat-health-sub').textContent =
                    hc === tc ? 'All systems nominal' : ` ${tc - hc} service${tc - hc > 1 ? 's' : ''} DOWN`;
                // Flash red border on health card if degraded

                const card = document.getElementById('stat-health')?.closest('.stat-card');
                if (card) {
                    card.style.borderColor = hc < tc ? 'var(--red)' : '';
                    card.style.boxShadow = hc < tc ? '0 0 20px rgba(255,51,102,0.4)' : '';
                }
                updateHealthGrid(health.services || {});
            }
        } catch (e) { }
    }, 2000));
    refreshTimers.push(setInterval(updateClock, 1000));
    refreshTimers.push(setInterval(updateHexTicker, 2000));
    updateClock();
    updateHexTicker();
}

// PAGE DATA LOADERS

async function loadPageData(page) {
    switch (page) {
        case 'overview': await loadOverview(); break;
        case 'attacks': await loadAttacks(); break;
        case 'honeypots': await loadHoneypots(); break;
        case 'models': await loadModels(); break;
        case 'adaptive': await aleRefresh(); break;
        case 'sitelogs': initSiteLogs(); loadSiteLogsData(); break;
        case 'blockchain': await loadBlockchain(); break;
        case 'canary': await loadCanary(); break;
        case 'fingerprints': await loadFingerprints(); break;
        case 'settings': await loadSettings(); break;
    }
}

// OVERVIEW

async function loadOverview() {
    try {
        const [stats, health, p2] = await Promise.all([
            fetch('/api/stats').then(r => r.json()).catch(() => ({})),
            fetch('/api/system-health').then(r => r.json()).catch(() => ({})),
            fetch('/api/phase2-stats').then(r => r.json()).catch(() => ({})),
        ]);

        animateValue('stat-attacks', stats.total_attacks || 0);
        animateValue('stat-honeypot', stats.total_honeypot_events || 0);
        const services = health.services || {};
        const filteredServices = Object.fromEntries(Object.entries(services).filter(([name]) => name !== 'SSH Honeypot'));
        const hc = Object.values(filteredServices).filter(s => s.status === 'healthy').length;
        const tc = Object.keys(filteredServices).length;

        document.getElementById('stat-health').textContent = tc > 0 ? `${hc}/${tc}` : '—';
        document.getElementById('stat-health-sub').textContent = hc === tc && tc > 0 ? 'All systems nominal' : tc > 0 ? 'Degraded' : 'Scanning...';
        const avgConf = stats.avg_confidence || 0;
        document.getElementById('stat-confidence').textContent = avgConf > 0 ? (avgConf * 100).toFixed(1) + '%' : '—';
        animateValue('stat-attackers', (stats.top_ips || []).length);
        document.getElementById('stat-attacks-sub').textContent = stats.last_attack ? `Last: ${new Date(stats.last_attack.timestamp).toLocaleTimeString()}` : 'Monitoring...';

        // Phase 2 stats

        const llm = p2.llm || {};
        document.getElementById('p2-llm-req').textContent = llm.requests || 0;
        document.getElementById('p2-llm-success').textContent = llm.success || 0;
        document.getElementById('p2-llm-fallback').textContent = llm.fallbacks || 0;
        const gan = p2.gan || {};
        document.getElementById('p2-gan-total').textContent = gan.total_users || 0;
        document.getElementById('p2-gan-pct').textContent = (gan.synthetic_pct || 0) + '% SYNTHETIC';
        document.getElementById('p2-gan-bar').style.width = (gan.synthetic_pct || 0) + '%';
        const fp = p2.fingerprints || {};
        document.getElementById('p2-fp-total').textContent = fp.total || 0;
        document.getElementById('p2-fp-clusters').textContent = fp.clusters || 0;

        // Charts

        updateChart(charts.attackType, stats.attack_types || {});
        updateTimelineChart(stats.hourly_attacks || {});
        updateMethodChart(stats.detection_methods || {});

        // IP Table

        updateIPTable(stats.top_ips || []);

        // Health grid

        updateHealthGrid(health.services || {});

        // Attack count badge

        attackCount = stats.total_attacks || 0;
        const badge = document.getElementById('attack-badge');
        if (badge) badge.textContent = attackCount;

    } catch (e) { console.error('Overview load error:', e); }

    // Load attack feed based on current tab
    await loadFeedData(currentFeedTab);
}

// LIVE THREAT FEED - Tab Switching
let currentFeedTab = 'recent';
let feedDataCache = {
    allAttacks: [],
    wazuhAlerts: [],
    lastFetch: 0
};

async function switchFeedTab(tab) {
    currentFeedTab = tab;

    // Update tab button styles
    document.querySelectorAll('.feed-tab-btn').forEach(btn => {
        if (btn.dataset.feedTab === tab) {
            btn.style.background = 'var(--cyan)';
            btn.style.color = '#000';
            btn.classList.add('active');
        } else {
            btn.style.background = 'rgba(255,255,255,0.1)';
            btn.style.color = 'var(--text-dim)';
            btn.classList.remove('active');
        }
    });

    // Load appropriate data
    await loadFeedData(tab);
}

async function loadFeedData(tab) {
    const now = Date.now();

    // Refresh cache if older than 5 seconds
    if (now - feedDataCache.lastFetch > 5000) {
        try {
            const [attacksData, wazuhData] = await Promise.all([
                fetch('/api/attacks?limit=200').then(r => r.json()).catch(() => ({ attacks: [] })),
                // API returns {alerts: [...], total: N} — extract the array
                fetch('/api/adaptive/wazuh-alerts?limit=100&min_level=3').then(r => r.json()).catch(() => ({ alerts: [] }))
            ]);
            feedDataCache.allAttacks = attacksData.attacks || [];
            // Handle both array (legacy) and object {alerts:[...]} response shapes
            feedDataCache.wazuhAlerts = Array.isArray(wazuhData)
                ? wazuhData
                : (wazuhData.alerts || []);
            feedDataCache.lastFetch = now;
        } catch (e) {
            console.error('Feed data fetch error:', e);
        }
    }

    switch (tab) {
        case 'recent':
            loadRecentFeed();
            break;
        case 'wazuh':
            loadWazuhFeed();
            break;
        case 'critical':
            loadCriticalFeed();
            break;
    }
}

function loadRecentFeed() {
    const allAttacks = feedDataCache.allAttacks;
    const fifteenMinutesAgo = Date.now() - (15 * 60 * 1000);
    const recentAttacks = allAttacks.filter(a => {
        const attackTime = new Date(a.timestamp).getTime();
        return attackTime >= fifteenMinutesAgo;
    });

    // Show only genuinely recent attacks — no silent fallback to historic data
    if (recentAttacks.length > 0) {
        updateFeed(recentAttacks.slice(0, 20));
        document.getElementById('feed-count').textContent = `${recentAttacks.length} live (last 15m)`;
    } else if (allAttacks.length > 0) {
        // Show latest 10 historical entries with a clear label so jury knows
        updateFeed(allAttacks.slice(0, 10));
        const lastTime = allAttacks[0]?.timestamp ? new Date(allAttacks[0].timestamp).toLocaleTimeString() : '';
        document.getElementById('feed-count').textContent = `No attacks in last 15m — showing latest (${lastTime})`;
    } else {
        updateFeed([]);
        document.getElementById('feed-count').textContent = '0 events';
    }
}

function loadWazuhFeed() {
    // Show level >= 5 security alerts; fall back to all >= 3 if no high-level ones
    const highAlerts = feedDataCache.wazuhAlerts.filter(a => a.rule_level >= 5);
    const allAlerts = feedDataCache.wazuhAlerts;
    const displayAlerts = highAlerts.length > 0 ? highAlerts.slice(0, 20) : allAlerts.slice(0, 20);
    updateWazuhFeed(displayAlerts);

    if (highAlerts.length > 0) {
        document.getElementById('feed-count').textContent = `${highAlerts.length} security alerts (${allAlerts.length} total ingested)`;
    } else if (allAlerts.length > 0) {
        document.getElementById('feed-count').textContent = `${allAlerts.length} Wazuh alerts (all system-level)`;
    } else {
        document.getElementById('feed-count').textContent = '0 Wazuh alerts ingested';
    }
}

function loadCriticalFeed() {
    const allAttacks = feedDataCache.allAttacks;
    const criticalAttacks = allAttacks.filter(a => {
        const conf = a.classification?.confidence || a.confidence || 0;
        return conf >= 0.75; // 75% confidence or higher
    }).sort((a, b) => {
        const ca = a.classification?.confidence || a.confidence || 0;
        const cb = b.classification?.confidence || b.confidence || 0;
        return cb - ca; // highest confidence first
    }).slice(0, 20);

    updateFeed(criticalAttacks);
    if (criticalAttacks.length > 0) {
        document.getElementById('feed-count').textContent = `${criticalAttacks.length} high severity (≥75% confidence)`;
    } else {
        document.getElementById('feed-count').textContent = 'No high severity attacks detected yet';
    }
}

function updateWazuhFeed(alerts) {
    const feed = document.getElementById('attack-feed');
    if (!feed) return;

    if (!alerts.length) {
        const totalAlerts = feedDataCache.wazuhAlerts.length;
        if (totalAlerts > 0) {
            feed.innerHTML = '<div class="feed-item"><div class="feed-icon info"></div><div class="feed-details"><div class="feed-path" style="color:var(--text-dim)">No security alerts (Level ≥5)</div><div class="feed-meta"><span>Showing only security-relevant alerts. ' + totalAlerts + ' system alerts hidden.</span></div></div></div>';
        } else {
            feed.innerHTML = '<div class="feed-item"><div class="feed-icon info"></div><div class="feed-details"><div class="feed-path" style="color:var(--text-dim)">No Wazuh alerts</div><div class="feed-meta"><span>SIEM alerts will appear here when detected</span></div></div></div>';
        }
        return;
    }

    feed.innerHTML = alerts.map(alert => {
        const time = new Date(alert.timestamp).toLocaleTimeString();
        const levelColor = alert.rule_level >= 10 ? 'var(--red)' : alert.rule_level >= 7 ? 'var(--yellow)' : 'var(--cyan)';
        const levelBadge = `<span class="badge" style="background:${levelColor};color:#000;font-weight:600">Level ${alert.rule_level}</span>`;
        const iconClass = alert.rule_level >= 10 ? 'danger' : alert.rule_level >= 7 ? 'warning' : 'info';

        return `<div class="feed-item">
            <div class="feed-icon ${iconClass}"></div>
            <div class="feed-details">
                <div class="feed-path">${alert.rule_description || 'Security Alert'}</div>
                <div class="feed-meta">
                    <span class="mono" style="color:var(--cyan)">${alert.ip || alert.agent_name || 'N/A'}</span>
                    <span>${time}</span>
                    <span style="color:var(--text-dim)">Rule ${alert.rule_id}</span>
                </div>
            </div>
            <div>${levelBadge}</div>
        </div>`;
    }).join('');
}

// ATTACKS

async function loadAttacks() {
    try {
        const data = await fetch('/api/attacks?limit=200').then(r => r.json());
        const tbody = document.getElementById('attacks-tbody');
        const attacks = (data.attacks || []).reverse();
        if (!attacks.length) {
            tbody.innerHTML = '<tr><td colspan="7" class="empty-state"><div class="empty-icon"></div><div class="empty-text">No attacks detected yet</div><div class="empty-sub">Launch attack simulations to see data here</div></td></tr>';
            return;
        }
        tbody.innerHTML = attacks.map((a, i) => {
            const cls = a.classification || {};
            let types = (cls.attack_types || []);
            // Fallback: use attack_type directly if classification.attack_types is empty
            if (!types.length && a.attack_type) {
                types = [a.attack_type];
            }
            const conf = cls.confidence || a.confidence || 0;
            const sev = conf > 0.8 ? 'critical' : conf > 0.5 ? 'high' : conf > 0.3 ? 'medium' : 'low';
            const badges = types.map(t => {
                const bc = BADGE_MAP[t.toLowerCase()] || 'badge-tool';
                return `<span class="badge ${bc}">${t}</span>`;
            }).join(' ');
            const method = cls.method || a.detection_method || '—';
            return `<tr>
                <td class="mono">${new Date(a.timestamp).toLocaleTimeString()}</td>
                <td class="mono" style="color:var(--cyan)">${a.ip || '—'}</td>
                <td><span style="color:var(--yellow)">${a.method || ''}</span> ${a.path || ''}</td>
                <td>${badges || '—'}</td>
                <td><span class="badge badge-${sev}">${sev}</span></td>
                <td style="color:${conf > 0.8 ? 'var(--red)' : conf > 0.5 ? 'var(--yellow)' : 'var(--cyan)'}">${(conf * 100).toFixed(0)}%</td>
                <td class="mono" style="font-size:0.68rem;color:var(--text-dim)">${method}</td>
            </tr>`;
        }).join('');
        document.getElementById('attacks-total').textContent = `${attacks.length} attacks`;
    } catch (e) { }
}

// HONEYPOTS

async function loadHoneypots() {
    try {
        // Get honeypot list
        const data = await fetch('/api/honeypots/list').then(r => r.json()).catch(() => ({}));
        const honeypots = (data.honeypots || []).filter(hp => hp.type !== 'ssh' && hp.name !== 'SSH Honeypot');

        // Update stats
        document.getElementById('hp-total').textContent = honeypots.length;
        document.getElementById('hp-online').textContent = data.online || 0;

        // Use total_attacks_captured from API (aligned with overview)
        const totalAttacks = data.total_attacks_captured || honeypots.reduce((sum, h) => sum + (h.attack_count || 0), 0);
        document.getElementById('hp-attacks').textContent = totalAttacks;

        const totalSessions = honeypots.reduce((sum, h) => sum + (h.active_sessions || 0), 0);
        document.getElementById('hp-sessions').textContent = totalSessions;

        // Get proxy config
        const proxyConfig = await fetch('/api/proxy/config').then(r => r.json()).catch(() => ({}));
        document.getElementById('rotation-interval').value = proxyConfig.rotation_interval || 60;
        document.getElementById('current-site').value = proxyConfig.current_site || 'banking';

        // Render honeypot cards
        const grid = document.getElementById('honeypot-grid');
        if (!honeypots.length) {
            grid.innerHTML = '<div class="empty-state"><div class="empty-icon"></div><div class="empty-text">No honeypots found</div></div>';
            return;
        }

        const icons = {
            'banking': '', 'ecommerce': '', 'healthcare': '', 'blog': '',
            'api_service': '', 'corporate': '', 'admin_panel': '', 'ssh': ''
        };

        grid.innerHTML = honeypots.map(hp => {
            const realUp = hp.real_status === 'online';
            const hpUp = hp.hp_status === 'online';
            const icon = icons[hp.type] || '';

            return `
            <div class="card">
                <div class="card-body">
                    <div style="display:flex;justify-content:space-between;align-items:start;margin-bottom:12px">
                        <div style="font-size:1.5rem">${icon}</div>
                        <span class="health-dot ${hpUp ? 'online' : 'offline'}"></span>
                    </div>
                    <div style="font-size:0.9rem;font-weight:600;color:var(--cyan);margin-bottom:8px">${hp.name}</div>
                    <div style="font-size:0.7rem;color:var(--text-dim);margin-bottom:12px">
                        <div><strong>Real:</strong> :${hp.real_port} <span class="health-dot ${realUp ? 'online' : 'offline'}" style="width:6px;height:6px"></span></div>
                        <div><strong>Honeypot:</strong> :${hp.hp_port} <span class="health-dot ${hpUp ? 'online' : 'offline'}" style="width:6px;height:6px"></span></div>
                    </div>
                    <button class="btn btn-outline" style="width:100%;padding:6px;font-size:0.7rem" onclick="viewHoneypotDetails('${hp.id}')">View Details</button>
                </div>
            </div>
            `;
        }).join('');

        // Load active sessions
        await loadActiveSessions();

        // Load routing rules
        await loadRoutingRules();

    } catch (e) {
        console.error('Failed to load honeypots:', e);
    }
}

async function refreshHoneypots() {
    await loadHoneypots();
}

async function viewHoneypotDetails(id) {
    try {
        // Show modal
        const modal = document.getElementById('honeypot-modal');
        modal.style.display = 'flex';

        // Fetch data
        const data = await fetch(`/api/honeypots/${id}/status`).then(r => r.json());

        // Update modal title
        document.getElementById('modal-honeypot-title').textContent = data.name;

        // Build content
        const content = `
            <div style="display:grid;grid-template-columns:1fr 1fr;gap:1.5rem;margin-bottom:1.5rem">
                <div>
                    <h4 style="font-family:'Orbitron',sans-serif;font-size:0.75rem;color:var(--text-muted);margin-bottom:0.75rem;text-transform:uppercase">Status</h4>
                    <div style="background:var(--bg-secondary);border-radius:8px;padding:1rem">
                        <div style="display:flex;justify-content:space-between;margin-bottom:0.5rem">
                            <span style="color:var(--text-dim);font-size:0.8rem">Real Site</span>
                            <span style="color:var(--cyan);font-weight:600;font-size:0.8rem">${data.real_status} (:${data.real_port})</span>
                        </div>
                        <div style="display:flex;justify-content:space-between">
                            <span style="color:var(--text-dim);font-size:0.8rem">Honeypot</span>
                            <span style="color:var(--green);font-weight:600;font-size:0.8rem">${data.hp_status} (:${data.hp_port})</span>
                        </div>
                    </div>
                </div>
                <div>
                    <h4 style="font-family:'Orbitron',sans-serif;font-size:0.75rem;color:var(--text-muted);margin-bottom:0.75rem;text-transform:uppercase">Statistics</h4>
                    <div style="background:var(--bg-secondary);border-radius:8px;padding:1rem">
                        <div style="display:flex;justify-content:space-between;margin-bottom:0.5rem">
                            <span style="color:var(--text-dim);font-size:0.8rem">Total Attacks</span>
                            <span style="color:var(--red);font-weight:600;font-size:0.8rem">${data.stats.total_attacks}</span>
                        </div>
                        <div style="display:flex;justify-content:space-between;margin-bottom:0.5rem">
                            <span style="color:var(--text-dim);font-size:0.8rem">Active Sessions</span>
                            <span style="color:var(--yellow);font-weight:600;font-size:0.8rem">${data.stats.active_sessions}</span>
                        </div>
                        <div style="display:flex;justify-content:space-between">
                            <span style="color:var(--text-dim);font-size:0.8rem">Canary Triggers</span>
                            <span style="color:var(--purple);font-weight:600;font-size:0.8rem">${data.stats.canary_triggers}</span>
                        </div>
                    </div>
                </div>
            </div>

            <div style="margin-bottom:1.5rem">
                <h4 style="font-family:'Orbitron',sans-serif;font-size:0.75rem;color:var(--text-muted);margin-bottom:0.75rem;text-transform:uppercase">Recent Attacks</h4>
                <div style="background:var(--bg-secondary);border-radius:8px;padding:1rem;max-height:200px;overflow-y:auto">
                    ${data.recent_attacks && data.recent_attacks.length > 0 ?
                data.recent_attacks.map(attack => `
                            <div style="padding:0.5rem;border-bottom:1px solid var(--border);font-size:0.75rem">
                                <div style="display:flex;justify-content:space-between;margin-bottom:0.25rem">
                                    <span style="color:var(--cyan);font-family:'JetBrains Mono',monospace">${attack.ip || 'Unknown'}</span>
                                    <span style="color:var(--text-dim)">${attack.timestamp || ''}</span>
                                </div>
                                <div style="color:var(--text-muted)">${attack.attack_type || 'Unknown'} - ${attack.path || '/'}</div>
                            </div>
                        `).join('')
                : '<div style="text-align:center;color:var(--text-dim);padding:1rem">No recent attacks</div>'
            }
                </div>
            </div>

            <div>
                <h4 style="font-family:'Orbitron',sans-serif;font-size:0.75rem;color:var(--text-muted);margin-bottom:0.75rem;text-transform:uppercase">Active Sessions</h4>
                <div style="background:var(--bg-secondary);border-radius:8px;padding:1rem;max-height:200px;overflow-y:auto">
                    ${data.active_sessions && data.active_sessions.length > 0 ?
                data.active_sessions.map(session => `
                            <div style="padding:0.5rem;border-bottom:1px solid var(--border);font-size:0.75rem">
                                <div style="display:flex;justify-content:space-between;margin-bottom:0.25rem">
                                    <span style="color:var(--cyan);font-family:'JetBrains Mono',monospace">${session.ip || 'Unknown'}</span>
                                    <span style="color:var(--text-dim)">Duration: ${session.duration || '0s'}</span>
                                </div>
                                <div style="color:var(--text-muted)">Requests: ${session.requests || 0} | Attacks: ${session.attacks || 0}</div>
                            </div>
                        `).join('')
                : '<div style="text-align:center;color:var(--text-dim);padding:1rem">No active sessions</div>'
            }
                </div>
            </div>
        `;

        document.getElementById('modal-honeypot-content').innerHTML = content;
    } catch (e) {
        console.error('Failed to load honeypot details:', e);
        document.getElementById('modal-honeypot-content').innerHTML = `
            <div style="text-align:center;padding:2rem;color:var(--red)">
                <div style="font-size:2rem;margin-bottom:1rem">⚠️</div>
                <div>Failed to load honeypot details</div>
            </div>
        `;
    }
}

function closeHoneypotModal() {
    document.getElementById('honeypot-modal').style.display = 'none';
}

// Close modal when clicking outside
document.addEventListener('click', function (e) {
    const modal = document.getElementById('honeypot-modal');
    if (modal && e.target === modal) {
        closeHoneypotModal();
    }
});

async function updateProxyConfig() {
    try {
        const config = {
            rotation_interval: parseInt(document.getElementById('rotation-interval').value),
            current_site: document.getElementById('current-site').value
        };

        const resp = await fetch('/api/proxy/config', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify(config)
        });

        if (resp.ok) {
            showToast('Proxy configuration updated', 'success');
        } else {
            showToast('Failed to update configuration', 'error');
        }
    } catch (e) {
        showToast('Error updating configuration', 'error');
    }
}

async function loadActiveSessions() {
    try {
        const data = await fetch('/api/sessions/active').then(r => r.json()).catch(() => ({ sessions: [] }));
        const sessions = data.sessions || [];

        const tbody = document.getElementById('sessions-tbody');
        if (!sessions.length) {
            tbody.innerHTML = '<tr><td colspan="7" class="empty-state"><div class="empty-icon"></div><div class="empty-text">No active sessions</div></td></tr>';
            return;
        }

        tbody.innerHTML = sessions.map(s => {
            const duration = s.duration_seconds || 0;
            const minutes = Math.floor(duration / 60);
            const seconds = duration % 60;
            const durationStr = `${minutes}m ${seconds}s`;

            const honeypots = s.honeypots_visited || [];
            const honeypotStr = honeypots.slice(0, 2).join(', ') + (honeypots.length > 2 ? '...' : '');

            return `<tr>
                <td class="mono" style="font-size:0.7rem">${s.session_id.substring(0, 8)}...</td>
                <td class="mono" style="color:var(--cyan)">${s.ip}</td>
                <td>${durationStr}</td>
                <td>${s.request_count || 0}</td>
                <td style="color:${s.attack_count > 0 ? 'var(--red)' : 'var(--text-dim)'}">${s.attack_count || 0}</td>
                <td style="font-size:0.7rem">${honeypotStr || 'None'}</td>
                <td><button class="btn btn-outline" style="padding:4px 8px;font-size:0.65rem" onclick="terminateSession(${s.id})">Terminate</button></td>
            </tr>`;
        }).join('');
    } catch (e) {
        console.error('Failed to load sessions:', e);
    }
}

async function terminateSession(sessionId) {
    if (!confirm('Terminate this session?')) return;

    try {
        const resp = await fetch(`/api/sessions/${sessionId}/terminate`, { method: 'POST' });
        if (resp.ok) {
            showToast('Session terminated', 'success');
            await loadActiveSessions();
        } else {
            showToast('Failed to terminate session', 'error');
        }
    } catch (e) {
        showToast('Error terminating session', 'error');
    }
}

async function loadRoutingRules() {
    try {
        const data = await fetch('/api/routing-rules/list').then(r => r.json()).catch(() => ({ rules: [] }));
        const rules = data.rules || [];

        const tbody = document.getElementById('rules-tbody');
        if (!rules.length) {
            tbody.innerHTML = '<tr><td colspan="6" class="empty-state"><div class="empty-icon"></div><div class="empty-text">No routing rules defined</div></td></tr>';
            return;
        }

        tbody.innerHTML = rules.map(r => {
            const conditions = r.conditions || {};
            const actions = r.actions || {};
            const condStr = Object.keys(conditions).slice(0, 2).join(', ') || 'None';
            const actStr = Object.keys(actions).slice(0, 2).join(', ') || 'None';

            return `<tr>
                <td style="font-weight:600">${r.name}</td>
                <td>${r.priority}</td>
                <td style="font-size:0.7rem">${condStr}</td>
                <td style="font-size:0.7rem">${actStr}</td>
                <td><span class="badge ${r.enabled ? 'badge-online' : 'badge-offline'}">${r.enabled ? 'Enabled' : 'Disabled'}</span></td>
            </tr>`;
        }).join('');
    } catch (e) {
        console.error('Failed to load routing rules:', e);
    }
}

function showCreateRuleModal() {
    const name = prompt('Rule Name:');
    if (!name) return;

    const description = prompt('Description (optional):') || '';
    const priority = parseInt(prompt('Priority (0-100):', '50')) || 50;

    createRoutingRule({ name, description, priority, enabled: true, conditions: {}, actions: {} });
}

async function createRoutingRule(rule) {
    try {
        const resp = await fetch('/api/routing-rules/create', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify(rule)
        });

        if (resp.ok) {
            showToast('Routing rule created', 'success');
            await loadRoutingRules();
        } else {
            showToast('Failed to create rule', 'error');
        }
    } catch (e) {
        showToast('Error creating rule', 'error');
    }
}

async function editRule(ruleId) {
    showToast('Rule editing: use the API directly for advanced changes.', 'info');
}

async function deleteRule(ruleId) {
    if (!confirm('Delete this routing rule?')) return;

    try {
        const resp = await fetch(`/api/routing-rules/${ruleId}/delete`, { method: 'DELETE' });
        if (resp.ok) {
            showToast('Rule deleted', 'success');
            await loadRoutingRules();
        } else {
            showToast('Failed to delete rule', 'error');
        }
    } catch (e) {
        showToast('Error deleting rule', 'error');
    }
}

// MODELS

async function loadModels() {
    try {
        const data = await fetch('/api/model-info').then(r => r.json());
        const wa = data.web_attack || {};
        const dd = data.ddos || {};
        const xss = data.xss || {};
        const bf = data.brute_force || {};
        const ps = data.port_scan || {};
        const cs = data.credential_stuffing || {};
        const an = data.anomaly || {};

        // Web Attack
        document.getElementById('wa-accuracy').textContent = ((wa.accuracy || 0) * 100).toFixed(1) + '%';
        document.getElementById('wa-precision').textContent = ((wa.precision || 0) * 100).toFixed(1) + '%';
        document.getElementById('wa-recall').textContent = ((wa.recall || 0) * 100).toFixed(1) + '%';
        document.getElementById('wa-f1').textContent = ((wa.f1_score || 0) * 100).toFixed(1) + '%';
        document.getElementById('wa-acc-bar').style.width = ((wa.accuracy || 0) * 100) + '%';
        document.getElementById('wa-prec-bar').style.width = ((wa.precision || 0) * 100) + '%';
        document.getElementById('wa-rec-bar').style.width = ((wa.recall || 0) * 100) + '%';
        document.getElementById('wa-f1-bar').style.width = ((wa.f1_score || 0) * 100) + '%';

        // DDoS
        document.getElementById('dd-accuracy').textContent = ((dd.accuracy || 0) * 100).toFixed(1) + '%';
        document.getElementById('dd-precision').textContent = ((dd.precision || 0) * 100).toFixed(1) + '%';
        document.getElementById('dd-recall').textContent = ((dd.recall || 0) * 100).toFixed(1) + '%';
        document.getElementById('dd-f1').textContent = ((dd.f1_score || 0) * 100).toFixed(1) + '%';
        document.getElementById('dd-acc-bar').style.width = ((dd.accuracy || 0) * 100) + '%';
        document.getElementById('dd-prec-bar').style.width = ((dd.precision || 0) * 100) + '%';
        document.getElementById('dd-rec-bar').style.width = ((dd.recall || 0) * 100) + '%';
        document.getElementById('dd-f1-bar').style.width = ((dd.f1_score || 0) * 100) + '%';

        // XSS
        document.getElementById('xss-accuracy').textContent = ((xss.accuracy || 0) * 100).toFixed(1) + '%';
        document.getElementById('xss-precision').textContent = ((xss.precision || 0) * 100).toFixed(1) + '%';
        document.getElementById('xss-recall').textContent = ((xss.recall || 0) * 100).toFixed(1) + '%';
        document.getElementById('xss-f1').textContent = ((xss.f1_score || 0) * 100).toFixed(1) + '%';
        document.getElementById('xss-acc-bar').style.width = ((xss.accuracy || 0) * 100) + '%';
        document.getElementById('xss-prec-bar').style.width = ((xss.precision || 0) * 100) + '%';
        document.getElementById('xss-rec-bar').style.width = ((xss.recall || 0) * 100) + '%';
        document.getElementById('xss-f1-bar').style.width = ((xss.f1_score || 0) * 100) + '%';

        // Brute Force
        document.getElementById('bf-accuracy').textContent = ((bf.accuracy || 0) * 100).toFixed(1) + '%';
        document.getElementById('bf-precision').textContent = ((bf.precision || 0) * 100).toFixed(1) + '%';
        document.getElementById('bf-recall').textContent = ((bf.recall || 0) * 100).toFixed(1) + '%';
        document.getElementById('bf-f1').textContent = ((bf.f1_score || 0) * 100).toFixed(1) + '%';
        document.getElementById('bf-acc-bar').style.width = ((bf.accuracy || 0) * 100) + '%';
        document.getElementById('bf-prec-bar').style.width = ((bf.precision || 0) * 100) + '%';
        document.getElementById('bf-rec-bar').style.width = ((bf.recall || 0) * 100) + '%';
        document.getElementById('bf-f1-bar').style.width = ((bf.f1_score || 0) * 100) + '%';

        // Port Scan
        document.getElementById('ps-accuracy').textContent = ((ps.accuracy || 0) * 100).toFixed(1) + '%';
        document.getElementById('ps-precision').textContent = ((ps.precision || 0) * 100).toFixed(1) + '%';
        document.getElementById('ps-recall').textContent = ((ps.recall || 0) * 100).toFixed(1) + '%';
        document.getElementById('ps-f1').textContent = ((ps.f1_score || 0) * 100).toFixed(1) + '%';
        document.getElementById('ps-acc-bar').style.width = ((ps.accuracy || 0) * 100) + '%';
        document.getElementById('ps-prec-bar').style.width = ((ps.precision || 0) * 100) + '%';
        document.getElementById('ps-rec-bar').style.width = ((ps.recall || 0) * 100) + '%';
        document.getElementById('ps-f1-bar').style.width = ((ps.f1_score || 0) * 100) + '%';

        // Credential Stuffing
        document.getElementById('cs-accuracy').textContent = ((cs.accuracy || 0) * 100).toFixed(1) + '%';
        document.getElementById('cs-precision').textContent = ((cs.precision || 0) * 100).toFixed(1) + '%';
        document.getElementById('cs-recall').textContent = ((cs.recall || 0) * 100).toFixed(1) + '%';
        document.getElementById('cs-f1').textContent = ((cs.f1_score || 0) * 100).toFixed(1) + '%';
        document.getElementById('cs-acc-bar').style.width = ((cs.accuracy || 0) * 100) + '%';
        document.getElementById('cs-prec-bar').style.width = ((cs.precision || 0) * 100) + '%';
        document.getElementById('cs-rec-bar').style.width = ((cs.recall || 0) * 100) + '%';
        document.getElementById('cs-f1-bar').style.width = ((cs.f1_score || 0) * 100) + '%';

        // Anomaly
        document.getElementById('an-accuracy').textContent = ((an.accuracy || 0) * 100).toFixed(1) + '%';
        document.getElementById('an-precision').textContent = ((an.precision || 0) * 100).toFixed(1) + '%';
        document.getElementById('an-recall').textContent = ((an.recall || 0) * 100).toFixed(1) + '%';
        document.getElementById('an-f1').textContent = ((an.f1_score || 0) * 100).toFixed(1) + '%';
        document.getElementById('an-acc-bar').style.width = ((an.accuracy || 0) * 100) + '%';
        document.getElementById('an-prec-bar').style.width = ((an.precision || 0) * 100) + '%';
        document.getElementById('an-rec-bar').style.width = ((an.recall || 0) * 100) + '%';
        document.getElementById('an-f1-bar').style.width = ((an.f1_score || 0) * 100) + '%';
    } catch (e) { }
}

// ═══════════════════════════════════════════════════════════
// ADAPTIVE LEARNING ENGINE
// ═══════════════════════════════════════════════════════════

const ALE_MODELS = ['XSS', 'Brute Force', 'Port Scan', 'Credential Stuffing', 'SQL Injection', 'DDoS', 'Anomaly Detection'];
const ALE_LEVEL_COLORS = { 0: 'var(--text-dim)', 5: 'var(--cyan)', 7: 'var(--yellow)', 10: 'var(--red)', 12: '#ff4444' };

function aleLevelColor(lvl) {
    if (lvl >= 12) return '#ff4444';
    if (lvl >= 10) return 'var(--red)';
    if (lvl >= 7) return 'var(--yellow)';
    if (lvl >= 5) return 'var(--cyan)';
    return 'var(--text-dim)';
}

async function aleRefresh() {
    await Promise.all([
        aleLoadStatus(),
        aleLoadTrainingStats(),
        loadWazuhAlerts(),
        aleLoadClusters(),
        aleLoadActiveAttacker(),
        aleLoadLiveStream(),
    ]);
    aleRenderRetrainControls();
}

async function aleLoadStatus() {
    try {
        const d = await fetch('/api/adaptive/status').then(r => r.json());
        const running = d.running !== false;
        document.getElementById('ale-status-badge').textContent = running ? 'RUNNING' : 'STOPPED';
        document.getElementById('ale-status-badge').style.color = running ? 'var(--green)' : 'var(--red)';
        document.getElementById('ale-wazuh-ingested').textContent = (d.wazuh_alerts_ingested || 0).toLocaleString();
        document.getElementById('ale-retrain-count').textContent = d.retraining_runs || 0;
        document.getElementById('ale-profiles-count').textContent = d.profiles_updated || 0;
    } catch (e) {
        document.getElementById('ale-status-badge').textContent = 'OFFLINE';
        document.getElementById('ale-status-badge').style.color = 'var(--text-dim)';
    }
}

async function aleLoadTrainingStats() {
    try {
        const d = await fetch('/api/adaptive/training-stats').then(r => r.json());
        document.getElementById('ale-total-samples').textContent = (d.total_samples || 0).toLocaleString();
        document.getElementById('ale-unused-samples').textContent = (d.unused_samples || 0).toLocaleString();
        document.getElementById('ale-wazuh-total').textContent = (d.wazuh_alerts_total || 0).toLocaleString();
        document.getElementById('ale-wazuh-unprocessed').textContent = (d.wazuh_unprocessed || 0).toLocaleString();

        const byType = d.by_attack_type || [];
        let html = '<table style="width:100%;font-size:0.72rem;border-collapse:collapse">';
        html += '<tr style="color:var(--text-dim)"><th style="text-align:left;padding:3px">Attack Type</th><th style="text-align:right;padding:3px">Samples</th><th style="text-align:right;padding:3px">Avg Conf</th></tr>';
        for (const row of byType) {
            html += `<tr style="border-top:1px solid var(--border)">
                <td style="padding:3px">${row.type || 'Unknown'}</td>
                <td style="text-align:right;padding:3px;color:var(--cyan)">${row.count}</td>
                <td style="text-align:right;padding:3px;color:var(--yellow)">${(row.avg_confidence * 100).toFixed(1)}%</td>
            </tr>`;
        }
        html += '</table>';
        document.getElementById('ale-by-type-table').innerHTML = html;
    } catch (e) { }
}

async function loadWazuhAlerts() {
    const level = document.getElementById('ale-wazuh-level-filter')?.value || 0;
    try {
        const d = await fetch(`/api/adaptive/wazuh-alerts?limit=100&min_level=${level}`).then(r => r.json());
        const tbody = document.getElementById('ale-wazuh-alerts-body');
        if (!d.alerts || !d.alerts.length) {
            tbody.innerHTML = '<tr><td colspan="6" style="color:var(--text-dim);text-align:center;padding:12px">No Wazuh alerts yet</td></tr>';
            return;
        }
        tbody.innerHTML = d.alerts.map(a => {
            const lvlColor = aleLevelColor(a.rule_level);
            const ts = a.timestamp ? a.timestamp.slice(11, 19) : '—';
            return `<tr style="border-top:1px solid var(--border)">
                <td style="padding:4px;color:var(--text-dim)">${ts}</td>
                <td style="padding:4px">${a.agent_name || '—'}</td>
                <td style="text-align:center;padding:4px;color:var(--text-dim)">${a.rule_id || '—'}</td>
                <td style="text-align:center;padding:4px;font-weight:700;color:${lvlColor}">${a.rule_level}</td>
                <td style="padding:4px;max-width:300px;overflow:hidden;text-overflow:ellipsis;white-space:nowrap">${a.rule_description || '—'}</td>
                <td style="padding:4px;color:var(--cyan)">${a.ip || '—'}</td>
            </tr>`;
        }).join('');
    } catch (e) { }
}

function aleRenderRetrainControls() {
    const container = document.getElementById('ale-retrain-controls');
    if (!container) return;
    container.innerHTML = ALE_MODELS.map(m => `
            <div style="display:flex;justify-content:space-between;align-items:center;background:var(--bg-card);border-radius:6px;padding:8px 12px">
            <span style="font-size:0.8rem;font-weight:600">${m}</span>
            <div style="display:flex;gap:6px">
                <button class="btn" style="font-size:0.7rem;padding:4px 10px;background:var(--cyan);color:#000"
                    onclick="aleTriggerRetrain('${m}')">↻ Retrain</button>
            </div>
        </div>`).join('');
}

async function aleTriggerRetrain(attackType) {
    const result = document.getElementById('ale-retrain-result');
    result.textContent = `Retraining ${attackType}...`;
    result.style.color = 'var(--yellow)';
    try {
        const d = await fetch('/api/adaptive/retrain', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ attack_type: attackType })
        }).then(r => r.json());
        const status = d.status || 'unknown';
        const acc = d.metrics ? ` → ${(d.metrics.accuracy * 100).toFixed(1)}% accuracy` : '';
        result.textContent = `${attackType}: ${status}${acc} `;
        result.style.color = status === 'retrain_queued' ? 'var(--green)' : 'var(--yellow)';
        // Refresh status to show updated counter
        setTimeout(() => aleLoadStatus(), 1000);
    } catch (e) {
        result.textContent = `Error: ${e.message} `;
        result.style.color = 'var(--red)';
    }
}

async function aleTriggerRollback(attackType) {
    const result = document.getElementById('ale-retrain-result');
    result.textContent = `Rolling back ${attackType}...`;
    result.style.color = 'var(--yellow)';
    try {
        const d = await fetch('/api/adaptive/rollback', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ attack_type: attackType })
        }).then(r => r.json());
        result.textContent = `${attackType}: ${d.status} ${d.restored_from || ''} `;
        result.style.color = d.status === 'rolled_back' ? 'var(--green)' : 'var(--red)';
    } catch (e) {
        result.textContent = `Error: ${e.message} `;
        result.style.color = 'var(--red)';
    }
}

async function aleLoadClusters() {
    const panel = document.getElementById('ale-clusters-panel');
    try {
        const data = await fetch('/api/adaptive/clusters').then(r => r.json());
        const clusters = data.clusters || [];

        if (!clusters.length) {
            panel.innerHTML = '<div style="color:var(--text-dim);text-align:center;padding:20px">No clusters yet — profiles are built as attacks accumulate</div>';
            return;
        }

        const colors = ['var(--cyan)', 'var(--purple)', 'var(--yellow)', 'var(--green)', 'var(--red)'];
        let html = '<div style="display:grid;grid-template-columns:repeat(auto-fill,minmax(180px,1fr));gap:12px">';

        clusters.forEach((c, i) => {
            const color = colors[i % colors.length];
            const attackTypes = c.attack_types ? c.attack_types.split(',').slice(0, 3).join(', ') : 'Various';

            html += `<div style="background:var(--bg-card);border-radius:8px;padding:12px;border-top:3px solid ${color}">
                <div style="font-weight:700;color:${color};margin-bottom:6px">Cluster ${c.cluster_id}</div>
                <div style="font-size:0.75rem"><span style="color:var(--text-dim)">Members:</span> <strong>${c.member_count}</strong></div>
                <div style="font-size:0.68rem;color:var(--text-dim);margin-top:4px;word-wrap:break-word">Types: ${attackTypes}</div>
            </div>`;
        });

        html += '</div>';
        panel.innerHTML = html;
    } catch (e) {
        console.error('Cluster load error:', e);
        panel.innerHTML = '<div style="color:var(--text-dim)">Cluster data unavailable</div>';
    }
}

async function aleLoadActiveAttacker() {
    const card = document.getElementById('ale-active-attacker-card');
    if (!card) return;
    try {
        const d = await fetch('/api/adaptive/active-attacker').then(r => r.json());
        if (!d.active) {
            card.innerHTML = '<div style="color:var(--text-dim);text-align:center;padding:30px">No active attackers currently monitored.</div>';
            return;
        }

        const scoreColor = d.threat_score > 0.7 ? 'var(--red)' : (d.threat_score > 0.4 ? 'var(--yellow)' : 'var(--cyan)');

        let html = `
            <div style="display:flex;justify-content:space-between;align-items:flex-start;margin-bottom:12px">
            <div>
                <div style="font-size:1.1rem;font-weight:700;color:var(--cyan);display:flex;align-items:center;gap:8px">
                    <span class="blinking-dot" style="background:var(--red)"></span>
                    ${escapeHtml(d.ip)}
                </div>
                <div style="font-size:0.75rem;color:var(--text-dim);margin-top:2px">
                    Last seen: ${escapeHtml(d.last_seen ? d.last_seen.replace('T', ' ').slice(0, 19) : '—')} 
                    (${escapeHtml(String(d.session_duration || 0))}s session)
                </div>
            </div>
            <div style="text-align:right">
                <div style="font-size:1.8rem;font-weight:700;color:${scoreColor};line-height:1">${(d.threat_score * 100).toFixed(0)}%</div>
                <div style="font-size:0.7rem;color:var(--text-dim)">THREAT SCORE</div>
            </div>
        </div>

        <div style="display:grid;grid-template-columns:1fr 1fr;gap:12px;margin-bottom:12px">
            <div style="background:rgba(0,0,0,0.2);padding:10px;border-radius:6px;border-left:2px solid var(--border)">
                <div style="font-size:0.7rem;color:var(--text-dim);margin-bottom:4px">CURRENT ATTACK</div>
                <div style="font-weight:600;color:var(--red)">${escapeHtml(d.attack_type || 'Unknown')}</div>
                <div style="font-size:0.75rem;color:var(--yellow);margin-top:2px">Conf: ${(d.confidence * 100).toFixed(1)}%</div>
            </div>
            <div style="background:rgba(0,0,0,0.2);padding:10px;border-radius:6px;border-left:2px solid var(--border)">
                <div style="font-size:0.7rem;color:var(--text-dim);margin-bottom:4px">TARGET</div>
                <div style="font-weight:600;color:${d.is_honeypot ? 'var(--yellow)' : 'var(--cyan)'}">
                    ${d.is_honeypot ? 'Honeypot' : 'Real Site'}
                </div>
                <div style="font-size:0.75rem;color:var(--text-dim);margin-top:2px">${escapeHtml(d.honeypot_name || '—')}</div>
            </div>
        </div>
        
        <div style="font-size:0.8rem;margin-bottom:12px">
            <span style="color:var(--text-dim)">User Agent:</span> ${escapeHtml(d.user_agent || '—')}
        </div>`;

        if (d.tools_detected && d.tools_detected.length > 0) {
            html += `<div style="margin-bottom:12px;font-size:0.8rem">
                <span style="color:var(--text-dim)">Tools Detected:</span> 
                <span style="color:var(--yellow)">${d.tools_detected.map(escapeHtml).join(', ')}</span>
            </div>`;
        }

        if (d.attack_types && d.attack_types.length > 0) {
            html += `<div style="margin-bottom:12px;font-size:0.8rem">
            <span style="color:var(--text-dim)">Historical Attacks:</span> 
                ${d.attack_types.map(escapeHtml).join(', ')}
            </div>`;
        }

        if (d.commands && d.commands.length > 0) {
            html += `<div style="font-size:0.75rem;color:var(--text-dim);margin-bottom:4px">Recent Commands / Paths:</div>
            <div style="flex:1;background:#0b1120;padding:8px;border-radius:4px;font-family:monospace;font-size:0.7rem;color:var(--green);min-height:80px;overflow-y:auto;border:1px solid #1e293b;margin-bottom:12px">
                ${d.commands.map(c => `<div>&gt; ${escapeHtml(c)}</div>`).join('')}
            </div>`;
        }

        if (d.wazuh_alerts && d.wazuh_alerts.length > 0) {
            html += `<div style="font-size:0.75rem;color:var(--text-dim);margin-bottom:4px">Triggered SIEM Rules:</div>
            <div style="display:flex;flex-direction:column;gap:4px">
                ${d.wazuh_alerts.map(w => `<div style="font-size:0.7rem;background:rgba(255,255,255,0.05);padding:4px 6px;border-radius:4px;border-left:2px solid ${aleLevelColor(w.rule_level)}">${escapeHtml(w.rule_description)} (Level ${w.rule_level})</div>`).join('')}
            </div>`;
        }

        card.innerHTML = html;
    } catch (e) {
        card.innerHTML = `<div style="color:var(--red);padding:20px;text-align:center">Failed to load active attacker data.</div>`;
    }
}

async function aleLoadLiveStream() {
    const streamBody = document.getElementById('ale-live-stream-body');
    if (!streamBody) return;
    try {
        const d = await fetch('/api/adaptive/live-stream?limit=20').then(r => r.json());
        if (!d.events || !d.events.length) {
            streamBody.innerHTML = '<div style="color:var(--text-dim);text-align:center;padding:20px">Awaiting live events...</div>';
            return;
        }

        let html = '';
        d.events.forEach(e => {
            const time = e.timestamp ? e.timestamp.slice(11, 19) : '—';
            let srcColor = e.source === 'wazuh' ? 'var(--blue)' : 'var(--yellow)';
            let targetHtml = e.source === 'wazuh'
                ? `<span style="color:var(--text-dim)">SIEM:</span> ${e.agent_name || 'System'}`
                : (e.is_honeypot
                    ? `<span style="color:var(--purple)">[HP]</span> ${e.honeypot_name}`
                    : `<span style="color:var(--cyan)">[REAL]</span> ${e.honeypot_name}`);

            let actionHtml = e.source === 'wazuh'
                ? `<span style="color:${aleLevelColor(e.rule_level)}">Alert L${e.rule_level}</span>`
                : `<span style="color:var(--green)">${(e.confidence * 100).toFixed(0)}%</span>`;

            html += `
            <div style="display:grid;grid-template-columns:60px 100px 120px 1fr 60px;gap:8px;padding:6px 0;border-bottom:1px solid rgba(255,255,255,0.05);font-size:0.75rem;align-items:center">
                <div style="color:var(--text-dim);font-family:monospace">${time}</div>
                <div style="color:${srcColor};white-space:nowrap;overflow:hidden;text-overflow:ellipsis">${e.ip || '—'}</div>
                <div style="font-weight:600;color:var(--red);white-space:nowrap;overflow:hidden;text-overflow:ellipsis">${e.attack_type || 'Event'}</div>
                <div style="white-space:nowrap;overflow:hidden;text-overflow:ellipsis">${targetHtml}</div>
                <div style="text-align:right">${actionHtml}</div>
            </div>`;
        });
        streamBody.innerHTML = html;
    } catch (e) {
        streamBody.innerHTML = `<div style="color:var(--red);padding:20px;text-align:center">Stream offline.</div>`;
    }
}


// BLOCKCHAIN

async function loadBlockchain() {
    try {
        const data = await fetch('/api/blockchain').then(r => r.json());
        const info = data.chain_info || {};
        document.getElementById('bc-total-blocks').textContent = info.total_blocks || 0;
        document.getElementById('bc-total-attacks').textContent = info.total_attacks || 0;
        const validEl = document.getElementById('bc-validity');
        validEl.className = data.is_valid !== false ? 'chain-valid' : 'chain-invalid';
        validEl.innerHTML = data.is_valid !== false ?
            ' Chain integrity verified — no tampering detected' :
            ' Chain integrity compromised — possible tampering';

        const list = document.getElementById('bc-blocks-list');
        const blocks = data.recent_blocks || [];
        if (!blocks.length) {
            list.innerHTML = '<div class="empty-state"><div class="empty-icon"></div><div class="empty-text">No blocks in the ledger yet</div><div class="empty-sub">Attack events will be recorded as immutable blockchain entries</div></div>';
            return;
        }
        list.innerHTML = blocks.reverse().map(b => {
            const d = b.data || {};
            const attackInfo = d.attack_types ? `<div style="margin-top:4px;font-size:0.72rem"><span style="color:var(--red)">${(d.attack_types || []).join(', ')}</span> <span style="color:var(--cyan)">← ${d.attacker_ip || d.ip || ''}</span> <span style="color:var(--text-dim)">${d.path || ''}</span></div>` : '';
            return `
            <div class="block-card">
                <div><span class="block-index">BLOCK #${b.index}</span>
                <span style="font-size:0.68rem;color:var(--text-dim)">${b.timestamp || ''}</span></div>
                <div class="block-hash" style="margin-top:6px">${b.hash || ''}</div>
                ${attackInfo}
        <div class="block-meta">prev: ${(b.previous_hash || '').substring(0, 20)}... | nonce: ${b.nonce || 0}</div>
            </div>
            `}).join('');
    } catch (e) { }
}

// CANARY

async function loadCanary() {
    try {
        const data = await fetch('/api/canary').then(r => r.json());
        document.getElementById('canary-total').textContent = data.total_triggers || 0;
        const byType = data.by_type || {};
        const typesGrid = document.getElementById('canary-types');
        const tokenTypes = [
            { type: 'env_file', label: 'ENV FILE', icon: '', desc: 'Fake environment variables' },
            { type: 'database_backup', label: 'BACKUP.SQL', icon: '', desc: 'Decoy database dumps' },
            { type: 'admin_panel_scan', label: 'WP-ADMIN', icon: '', desc: 'Fake WordPress panel' },
            { type: 'phpmyadmin_scan', label: 'PHPMYADMIN', icon: '', desc: 'Decoy database manager' },
            { type: 'api_config', label: 'API CONFIG', icon: '', desc: 'Fake API credentials' },
            { type: 'git_exposure', label: '.GIT/CONFIG', icon: '', desc: 'Repository exposure trap' },
            { type: 'server_status', label: 'SERVER-STATUS', icon: '', desc: 'Apache status page' },
            { type: 'debug_endpoint', label: 'DEBUG ENDPOINT', icon: '', desc: 'Fake debug information' },
            { type: 'eicar_scare', label: 'EICAR SCARE', icon: '', desc: 'Antivirus tripwire' },
            { type: 'zip_bomb_download', label: 'ZIP BOMB', icon: '', desc: 'Decompression trap' },
        ];
        typesGrid.innerHTML = tokenTypes.map(t => `
            <div class="stat-card cyan" style="padding:1rem">
                <div style="font-size:1.5rem;margin-bottom:6px">${t.icon}</div>
                <div class="stat-label">${t.label}</div>
                <div class="stat-value" style="font-size:1.4rem">${byType[t.type] || 0}</div>
                <div class="stat-sub">${t.desc}</div>
            </div>
            `).join('');

        const alertsList = document.getElementById('canary-alerts');
        const alerts = data.recent_alerts || [];
        if (!alerts.length) {
            alertsList.innerHTML = '<div class="empty-state"><div class="empty-icon"></div><div class="empty-text">No canary triggers yet</div><div class="empty-sub">Canary tokens are deployed and waiting for attacker interaction</div></div>';
            return;
        }
        alertsList.innerHTML = alerts.slice(-15).reverse().map(a => `
            <div class="feed-item">
                <div class="feed-icon warning"></div>
                <div class="feed-details">
                    <div class="feed-path">${a.token_type || 'unknown'} triggered</div>
                    <div class="feed-meta"><span>${a.attacker_ip || a.ip || ''}</span><span>${a.timestamp ? new Date(a.timestamp).toLocaleString() : ''}</span></div>
                </div>
            </div>
            `).join('');
    } catch (e) { }
}

// FINGERPRINTS

async function loadFingerprints() {
    try {
        const data = await fetch('/api/fingerprints').then(r => r.json());

        // Update stats
        document.getElementById('fp-total').textContent = data.total || 0;
        document.getElementById('fp-clusters').textContent = data.clusters || 0;

        // Render cluster table
        const clusterTbody = document.getElementById('fp-clusters-tbody');
        const clusters = data.clusters_data || [];
        if (!clusters.length) {
            clusterTbody.innerHTML = '<tr><td colspan="6" class="empty-state"><div class="empty-icon">🎯</div><div class="empty-text">No clusters formed yet</div><div class="empty-sub">Clusters will appear as attackers interact with honeypots</div></td></tr>';
        } else {
            clusterTbody.innerHTML = clusters.map(c => {
                const countries = (c.countries || []).join(', ') || 'Unknown';
                const cities = (c.cities || []).join(', ') || 'Unknown';

                return `
            <tr>
                        <td><span class="badge badge-online">Cluster ${c.cluster_id}</span></td>
                        <td>${c.member_count || 0}</td>
                        <td>${c.unique_fingerprints || 0}</td>
                        <td style="font-size:0.75rem">
                            <div style="color:var(--text-primary)">${countries}</div>
                            <div style="color:var(--text-dim);font-size:0.68rem">${cities}</div>
                        </td>
                        <td class="mono" style="font-size:0.68rem;color:var(--text-dim)">${c.first_seen ? new Date(c.first_seen).toLocaleString() : '—'}</td>
                        <td class="mono" style="font-size:0.68rem;color:var(--text-dim)">${c.last_seen ? new Date(c.last_seen).toLocaleString() : '—'}</td>
                    </tr>
            `;
            }).join('');
        }

        // Render profiles table
        const tbody = document.getElementById('fp-tbody');
        const profiles = data.profiles || [];
        if (!profiles.length) {
            tbody.innerHTML = '<tr><td colspan="6" class="empty-state"><div class="empty-icon">🔍</div><div class="empty-text">No fingerprints collected yet</div><div class="empty-sub">Behavioral data will appear when attackers interact with honeypots</div></td></tr>';
            return;
        }

        tbody.innerHTML = profiles.map(p => {
            const ips = (p.ips_used || []).slice(0, 3).join(', ');
            const moreIps = (p.ips_used || []).length > 3 ? ` +${(p.ips_used || []).length - 3}` : '';

            // Get JA3 from behavioral_hash if available
            const ja3Display = p.ja3_hash || p.behavioral_hash
                ? `<span class="mono" style="font-size:0.7rem;color:var(--cyan)">${(p.ja3_hash || p.behavioral_hash).substring(0, 16)}...</span>`
                : '<span style="color:var(--text-dim);font-size:0.7rem">N/A</span>';

            const clusterBadge = p.cluster_id !== null && p.cluster_id !== undefined
                ? `<span class="badge badge-online">C${p.cluster_id}</span>`
                : '<span style="color:var(--text-dim)">—</span>';

            const sessions = p.attack_count || p.profile_count || 0;

            return `
            <tr>
                    <td class="mono" style="font-size:0.75rem">${p.behavioral_hash}</td>
                    <td style="font-size:0.75rem">
                        <div>${ips}${moreIps}</div>
                    </td>
                    <td>${ja3Display}</td>
                    <td>${clusterBadge}</td>
                    <td>${sessions}</td>
                    <td class="mono" style="font-size:0.68rem;color:var(--text-dim)">${p.last_seen ? new Date(p.last_seen).toLocaleString() : '—'}</td>
                </tr>
            `;
        }).join('');
    } catch (e) {
        console.error('Failed to load fingerprints:', e);
    }
}

// SETTINGS

async function loadSettings() {
    try {
        const data = await fetch('/api/settings').then(r => r.json());
        document.getElementById('set-rotation').value = data.rotation_interval || 60;
        document.getElementById('set-site').value = data.default_site || 'banking';
        document.getElementById('set-notif').checked = data.notifications_enabled !== false;
        document.getElementById('set-autorefresh').checked = data.auto_refresh !== false;
        document.getElementById('set-interval').value = data.refresh_interval || 5;
    } catch (e) { }
}

async function saveSettings() {
    const data = {
        rotation_interval: parseInt(document.getElementById('set-rotation').value) || 60,
        default_site: document.getElementById('set-site').value,
        notifications_enabled: document.getElementById('set-notif').checked,
        auto_refresh: document.getElementById('set-autorefresh').checked,
        refresh_interval: parseInt(document.getElementById('set-interval').value) || 5,
    };
    try {
        await fetch('/api/settings', {
            method: 'POST', headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify(data)
        });
        const btn = document.getElementById('save-settings-btn');
        btn.textContent = ' SAVED';
        setTimeout(() => btn.textContent = 'SAVE CHANGES', 2000);
    } catch (e) { }
}

// CHARTS

function initCharts() {
    const chartOpts = { responsive: true, maintainAspectRatio: false };

    charts.attackType = new Chart(document.getElementById('attackTypeChart'), {
        type: 'doughnut',
        data: {
            labels: ['SQLi', 'XSS', 'NoSQLi', 'Traversal', 'Tool'],
            datasets: [{ data: [0, 0, 0, 0, 0], backgroundColor: COLORS, borderWidth: 0, hoverOffset: 8 }]
        },
        options: {
            ...chartOpts, cutout: '70%',
            plugins: { legend: { position: 'right', labels: { padding: 14, usePointStyle: true, pointStyle: 'circle', font: { family: "'JetBrains Mono',monospace", size: 10 } } } }
        }
    });

    charts.timeline = new Chart(document.getElementById('timelineChart'), {
        type: 'bar',
        data: {
            labels: [], datasets: [{
                label: 'Threats', data: [],
                backgroundColor: 'rgba(0,240,255,0.25)', borderColor: '#00f0ff', borderWidth: 1, borderRadius: 4
            }]
        },
        options: {
            ...chartOpts,
            plugins: { legend: { display: false } },
            scales: {
                y: { beginAtZero: true, grid: { color: 'rgba(0,240,255,0.04)' }, ticks: { stepSize: 1, font: { family: "'JetBrains Mono',monospace", size: 10 } } },
                x: { grid: { display: false }, ticks: { font: { family: "'JetBrains Mono',monospace", size: 10 } } }
            }
        }
    });

    charts.method = new Chart(document.getElementById('methodChart'), {
        type: 'bar',
        data: {
            labels: ['Rule-Based', 'ML API', 'Known Attacker', 'Fallback'],
            datasets: [{ label: 'Detections', data: [0, 0, 0, 0], backgroundColor: ['#00f0ff', '#00ff88', '#ff3366', '#ffaa00'], borderRadius: 6 }]
        },
        options: {
            ...chartOpts, indexAxis: 'y',
            plugins: { legend: { display: false } },
            scales: {
                x: { beginAtZero: true, grid: { color: 'rgba(0,240,255,0.04)' }, ticks: { font: { family: "'JetBrains Mono',monospace", size: 10 } } },
                y: { grid: { display: false }, ticks: { font: { family: "'JetBrains Mono',monospace", size: 10 } } }
            }
        }
    });
}

function updateChart(chart, dataObj) {
    if (!chart) return;
    chart.data.labels = Object.keys(dataObj);
    chart.data.datasets[0].data = Object.values(dataObj);
    chart.data.datasets[0].backgroundColor = Object.keys(dataObj).map((_, i) => COLORS[i % COLORS.length]);
    chart.update();
}
function updateTimelineChart(dataObj) {
    if (!charts.timeline) return;
    charts.timeline.data.labels = Object.keys(dataObj);
    charts.timeline.data.datasets[0].data = Object.values(dataObj);
    charts.timeline.update();
}
function updateMethodChart(dataObj) {
    if (!charts.method) return;
    charts.method.data.labels = Object.keys(dataObj);
    charts.method.data.datasets[0].data = Object.values(dataObj);
    charts.method.update();
}

// UI HELPERS

function animateValue(id, target) {
    const el = document.getElementById(id);
    if (!el) return;
    const current = parseInt(el.textContent) || 0;
    if (current === target) return;
    const step = Math.ceil(Math.abs(target - current) / 20);
    let val = current;
    const timer = setInterval(() => {
        val += val < target ? step : -step;
        if ((step > 0 && val >= target) || (step < 0 && val <= target)) { val = target; clearInterval(timer); }
        el.textContent = val;
    }, 30);
}

function updateFeed(attacks) {
    const feed = document.getElementById('attack-feed');
    if (!feed) return;
    if (!attacks.length) {
        const emptyMessages = {
            'recent': '<div class="feed-item"><div class="feed-icon info"></div><div class="feed-details"><div class="feed-path" style="color:var(--text-dim)">No attacks in database</div><div class="feed-meta"><span>Generate attacks to see live detections</span></div></div></div>',
            'critical': '<div class="feed-item"><div class="feed-icon info"></div><div class="feed-details"><div class="feed-path" style="color:var(--text-dim)">No high severity threats</div><div class="feed-meta"><span>Attacks with 75%+ confidence will appear here</span></div></div></div>',
            'wazuh': '<div class="feed-item"><div class="feed-icon info"></div><div class="feed-details"><div class="feed-path" style="color:var(--text-dim)">No Wazuh alerts</div><div class="feed-meta"><span>SIEM alerts will appear here</span></div></div></div>'
        };
        feed.innerHTML = emptyMessages[currentFeedTab] || emptyMessages['recent'];
        return;
    }
    feed.innerHTML = attacks.reverse().map(a => {
        const cl = a.classification || {};
        let types = cl.attack_types || [];
        if (!types.length && a.attack_type) types = [a.attack_type];
        const time = new Date(a.timestamp).toLocaleTimeString();
        const badges = types.map(t => {
            const bc = BADGE_MAP[t.toLowerCase()] || 'badge-tool';
            return `<span class="badge ${bc}">${t}</span>`;
        }).join(' ');
        const conf = cl.confidence || a.confidence || 0;

        // Use glowing red square icon for Recent and High Severity tabs
        const iconClass = (currentFeedTab === 'recent' || currentFeedTab === 'critical') ? 'danger-glow' : 'danger';

        return `<div class="feed-item">
            <div class="feed-icon ${iconClass}"></div>
            <div class="feed-details">
                <div class="feed-path">${a.method} ${a.path}</div>
                <div class="feed-meta">
                    <span class="mono" style="color:var(--cyan)">${a.ip}</span>
                    <span>${time}</span>
                    <span style="color:${conf > 0.8 ? 'var(--red)' : conf > 0.5 ? 'var(--yellow)' : 'var(--cyan)'}"> ${(conf * 100).toFixed(0)}%</span>
                </div>
            </div>
            <div>${badges}</div>
        </div>`;
    }).join('');
}

function updateIPTable(ips) {
    const tbody = document.getElementById('ip-table-body');
    if (!tbody) return;
    if (!ips.length) {
        tbody.innerHTML = '<tr><td colspan="3" style="text-align:center;color:var(--text-dim);padding:2rem;font-size:0.8rem">No threat actors identified</td></tr>';
        return;
    }
    const max = Math.max(...ips.map(i => i.count));
    tbody.innerHTML = ips.map(ip => {
        const pct = (ip.count / max * 100).toFixed(0);
        const color = pct > 75 ? 'var(--red)' : pct > 40 ? 'var(--yellow)' : 'var(--cyan)';
        const lastSeen = ip.last_seen ? new Date(ip.last_seen).toLocaleTimeString() : '';
        return `<tr>
            <td class="mono">${ip.ip}</td>
            <td><strong style="color:${color}">${ip.count}</strong> <span style="font-size:0.6rem;color:var(--text-dim)">${lastSeen}</span></td>
            <td><div class="threat-bar"><div class="threat-fill" style="width:${pct}%;background:${color};color:${color}"></div></div></td>
        </tr>`;
    }).join('');
}

function updateHealthGrid(services) {
    const grid = document.getElementById('health-grid');
    if (!grid) return;
    if (!Object.keys(services).length) {
        grid.innerHTML = '<div class="health-item"><div class="health-dot offline"></div><span class="health-name">scanning...</span></div>';
        return;
    }
    grid.innerHTML = Object.entries(services)
        .filter(([name]) => name !== 'SSH Honeypot')
        .map(([name, info]) => `
            <div class="health-item">
            <div class="health-dot ${info.status === 'healthy' ? 'online' : 'offline'}"></div>
            <span class="health-name">${name}</span>
            <span class="health-port">:${info.port || ''}</span>
        </div>
            `).join('');
}

function updateHexTicker() {
    const el = document.getElementById('hex-ticker');
    if (!el) return;
    const hex = Array.from({ length: 8 }, () => Math.floor(Math.random() * 256).toString(16).padStart(2, '0').toUpperCase()).join(' ');
    el.textContent = `0x${hex} — MONITORING ACTIVE`;
}

function updateClock() {
    const el = document.getElementById('clock');
    if (!el) return;
    el.textContent = new Date().toLocaleTimeString('en-US', { hour12: false, hour: '2-digit', minute: '2-digit', second: '2-digit' });
}

// BOOT

document.addEventListener('DOMContentLoaded', () => {
    checkSession();
    // Enter key on login

    document.getElementById('login-pass')?.addEventListener('keypress', e => { if (e.key === 'Enter') doLogin(); });
    document.getElementById('login-user')?.addEventListener('keypress', e => { if (e.key === 'Enter') document.getElementById('login-pass').focus(); });
});


// ============================================================================
// NEW PAGES: Attack History, Attacker Profiles
// ============================================================================

// ATTACK HISTORY

let attackHistoryData = [];
let filteredAttacks = [];
let currentPageNum = 1;
const pageSize = 50;
let currentSortField = 'timestamp';
let currentSortOrder = 'desc';

async function loadAttackHistory() {
    try {
        const resp = await fetch('/api/attack-history/list?limit=1000');
        const data = await resp.json();
        attackHistoryData = data.attacks || [];

        // Parse JSON fields
        attackHistoryData.forEach(a => {
            if (typeof a.attack_types === 'string') {
                try { a.attack_types = JSON.parse(a.attack_types); } catch (e) { }
            }
            if (typeof a.classification === 'string') {
                try { a.classification = JSON.parse(a.classification); } catch (e) { }
            }
            if (!a.classification) {
                a.classification = {
                    attack_types: a.attack_types || [a.attack_type],
                    confidence: a.confidence || 0,
                    method: a.detection_method || 'unknown'
                };
            }
        });

        filteredAttacks = [...attackHistoryData];

        // Update stats
        document.getElementById('ah-total').textContent = attackHistoryData.length;
        document.getElementById('ah-filtered').textContent = filteredAttacks.length;

        const uniqueIPs = new Set(attackHistoryData.map(a => a.ip)).size;
        document.getElementById('ah-unique-ips').textContent = uniqueIPs;

        const avgConf = attackHistoryData.length > 0
            ? (attackHistoryData.reduce((sum, a) => sum + (a.confidence || 0), 0) / attackHistoryData.length * 100).toFixed(1)
            : 0;
        document.getElementById('ah-avg-conf').textContent = avgConf + '%';

        renderAttackTable();
    } catch (e) {
        console.error('Failed to load attack history:', e);
    }
}

function filterAttacks() {
    const typeFilter = document.getElementById('filter-type')?.value || '';
    const severityFilter = document.getElementById('filter-severity')?.value || '';
    const ipFilter = document.getElementById('filter-ip')?.value || '';
    const dateFilter = document.getElementById('filter-date')?.value || '';

    filteredAttacks = attackHistoryData.filter(attack => {
        // Type filter
        if (typeFilter && typeFilter !== '') {
            const attackType = attack.attack_type || '';
            const types = attack.classification?.attack_types || [];
            const allTypes = [attackType, ...types].map(t => String(t).toLowerCase());
            if (!allTypes.some(t => t.includes(typeFilter.toLowerCase()))) return false;
        }

        // Severity filter
        if (severityFilter && severityFilter !== '') {
            const conf = attack.confidence || attack.classification?.confidence || 0;
            const sev = conf > 0.8 ? 'critical' : conf > 0.5 ? 'high' : conf > 0.3 ? 'medium' : 'low';
            if (sev !== severityFilter.toLowerCase()) return false;
        }

        // IP filter
        if (ipFilter && ipFilter !== '') {
            const ip = attack.ip || '';
            if (!ip.toLowerCase().includes(ipFilter.toLowerCase())) return false;
        }

        // Date filter
        if (dateFilter && dateFilter !== '') {
            const now = new Date();
            const attackTime = new Date(attack.timestamp);
            const diffMs = now - attackTime;
            const diffHours = diffMs / (1000 * 60 * 60);

            if (dateFilter === '1h' && diffHours > 1) return false;
            if (dateFilter === '24h' && diffHours > 24) return false;
            if (dateFilter === '7d' && diffHours > 168) return false;
            if (dateFilter === '30d' && diffHours > 720) return false;
        }

        return true;
    });

    document.getElementById('ah-filtered').textContent = filteredAttacks.length;
    currentPageNum = 1;
    sortAttacks(currentSortField, currentSortOrder);
    renderAttackTable();
}

function sortAttacks(field, order) {
    currentSortField = field;
    currentSortOrder = order || currentSortOrder;

    filteredAttacks.sort((a, b) => {
        let valA, valB;

        if (field === 'timestamp') {
            valA = new Date(a.timestamp).getTime();
            valB = new Date(b.timestamp).getTime();
        } else if (field === 'ip') {
            valA = a.ip || '';
            valB = b.ip || '';
        } else if (field === 'attack_type') {
            valA = a.attack_type || '';
            valB = b.attack_type || '';
        } else if (field === 'severity') {
            const confA = a.confidence || a.classification?.confidence || 0;
            const confB = b.confidence || b.classification?.confidence || 0;
            valA = confA;
            valB = confB;
        } else if (field === 'confidence') {
            valA = a.confidence || a.classification?.confidence || 0;
            valB = b.confidence || b.classification?.confidence || 0;
        } else {
            return 0;
        }

        if (currentSortOrder === 'asc') {
            return valA > valB ? 1 : valA < valB ? -1 : 0;
        } else {
            return valA < valB ? 1 : valA > valB ? -1 : 0;
        }
    });

    renderAttackTable();
}

function toggleSort(field) {
    if (currentSortField === field) {
        currentSortOrder = currentSortOrder === 'asc' ? 'desc' : 'asc';
    } else {
        currentSortField = field;
        currentSortOrder = 'desc';
    }
    sortAttacks(field, currentSortOrder);
}

function clearFilters() {
    if (document.getElementById('filter-type')) document.getElementById('filter-type').value = '';
    if (document.getElementById('filter-severity')) document.getElementById('filter-severity').value = '';
    if (document.getElementById('filter-ip')) document.getElementById('filter-ip').value = '';
    if (document.getElementById('filter-date')) document.getElementById('filter-date').value = '';
    filterAttacks();
}

function renderAttackTable() {
    const tbody = document.getElementById('attack-history-tbody');
    const start = (currentPageNum - 1) * pageSize;
    const end = start + pageSize;
    const pageData = filteredAttacks.slice(start, end);

    if (pageData.length === 0) {
        tbody.innerHTML = '<tr><td colspan="8" class="empty-state"><div class="empty-icon"></div><div class="empty-text">No attacks match filters</div></td></tr>';
        return;
    }

    tbody.innerHTML = pageData.map(a => {
        const cls = a.classification || {};
        const types = cls.attack_types || [];
        const conf = cls.confidence || 0;
        const sev = conf > 0.8 ? 'critical' : conf > 0.5 ? 'high' : conf > 0.3 ? 'medium' : 'low';
        const badges = types.map(t => {
            const bc = BADGE_MAP[t.toLowerCase()] || 'badge-tool';
            return `<span class="badge ${bc}">${t}</span>`;
        }).join(' ');

        return `<tr>
            <td class="mono" style="font-size:0.75rem">${new Date(a.timestamp).toLocaleString()}</td>
            <td class="mono" style="color:var(--cyan)">${a.ip || '—'}</td>
            <td><span style="color:var(--yellow)">${a.method || ''}</span> ${(a.path || '').substring(0, 40)}${a.path?.length > 40 ? '...' : ''}</td>
            <td>${badges || '—'}</td>
            <td><span class="badge badge-${sev}">${sev}</span></td>
            <td style="color:${conf > 0.8 ? 'var(--red)' : conf > 0.5 ? 'var(--yellow)' : 'var(--cyan)'}">${(conf * 100).toFixed(0)}%</td>
            <td class="mono" style="font-size:0.68rem;color:var(--text-dim)">${cls.method || '—'}</td>
            <td><button class="btn btn-outline" style="padding:4px 8px;font-size:0.65rem" onclick="viewAttackDetail(${a.id})">View</button></td>
        </tr>`;
    }).join('');

    // Update pagination
    const totalPages = Math.ceil(filteredAttacks.length / pageSize);
    document.getElementById('page-info').textContent = `Page ${currentPageNum} of ${totalPages}`;
    document.getElementById('btn-prev').disabled = currentPageNum === 1;
    document.getElementById('btn-next').disabled = currentPageNum >= totalPages;
}

function prevPage() {
    if (currentPageNum > 1) {
        currentPageNum--;
        renderAttackTable();
    }
}

function nextPage() {
    const totalPages = Math.ceil(filteredAttacks.length / pageSize);
    if (currentPageNum < totalPages) {
        currentPageNum++;
        renderAttackTable();
    }
}

async function viewAttackDetail(id) {
    try {
        const resp = await fetch(`/api/attack-history/${id}`);
        const data = await resp.json();
        const cls = data.classification || {};
        const conf = (cls.confidence || data.confidence || 0) * 100;
        showToast(
            `ID #${data.id} | ${data.method} ${data.path}\nIP: ${data.ip} | ${new Date(data.timestamp).toLocaleTimeString()}\nType: ${(cls.attack_types || [data.attack_type || 'Unknown']).join(', ')} | Conf: ${conf.toFixed(0)}%`,
            'info', 6000
        );
    } catch (e) {
        showToast('Failed to load attack details', 'error');
    }
}

async function exportAttacks(format) {
    try {
        // Build query params with current filters
        const typeFilter = document.getElementById('filter-type')?.value || '';
        const severityFilter = document.getElementById('filter-severity')?.value || '';
        const ipFilter = document.getElementById('filter-ip')?.value || '';
        const dateFilter = document.getElementById('filter-date')?.value || '';

        let url = `/api/attack-history/export?format=${format}`;
        if (typeFilter) url += `&attack_type=${encodeURIComponent(typeFilter)}`;
        if (ipFilter) url += `&ip=${encodeURIComponent(ipFilter)}`;

        const resp = await fetch(url);
        if (!resp.ok) throw new Error('Export failed');

        const blob = await resp.blob();
        const downloadUrl = window.URL.createObjectURL(blob);
        const a = document.createElement('a');
        a.href = downloadUrl;
        a.download = `attack_history_${new Date().toISOString().split('T')[0]}.${format}`;
        document.body.appendChild(a);
        a.click();
        document.body.removeChild(a);
        window.URL.revokeObjectURL(downloadUrl);
    } catch (e) {
        console.error('Export failed:', e);
        showToast('Export failed. Please try again.', 'error');
    }
}

// ATTACKER PROFILES

let profilesData = [];
let clusterChartObj = null;

async function loadAttackerProfiles() {
    try {
        const resp = await fetch('/api/attacker-profiles/list');
        const data = await resp.json();
        profilesData = data.profiles || [];

        // Update stats
        document.getElementById('ap-total').textContent = profilesData.length;
        document.getElementById('ap-clusters').textContent = data.cluster_count || 0;

        const highRisk = profilesData.filter(p => (p.threat_score || 0) > 0.7).length;
        document.getElementById('ap-high-risk').textContent = highRisk;

        const today = new Date().toISOString().split('T')[0];
        const activeToday = profilesData.filter(p => p.last_seen?.startsWith(today)).length;
        document.getElementById('ap-active-today').textContent = activeToday;

        // Render cluster chart
        renderClusterChart(data.clusters || {});

        // Render profile cards
        renderProfileCards();
    } catch (e) {
        console.error('Failed to load attacker profiles:', e);
    }
}

function renderClusterChart(clusters) {
    const ctx = document.getElementById('clusterChart');
    if (!ctx) return;

    if (clusterChartObj) {
        clusterChartObj.destroy();
    }

    const labels = Object.keys(clusters);
    const values = Object.values(clusters);

    clusterChartObj = new Chart(ctx, {
        type: 'bar',
        data: {
            labels: labels.map(l => `Cluster ${l} `),
            datasets: [{
                label: 'Attackers',
                data: values,
                backgroundColor: COLORS,
                borderRadius: 6
            }]
        },
        options: {
            responsive: true,
            maintainAspectRatio: false,
            plugins: { legend: { display: false } },
            scales: {
                y: { beginAtZero: true, grid: { color: 'rgba(0,240,255,0.04)' } },
                x: { grid: { display: false } }
            }
        }
    });
}

function renderProfileCards() {
    const container = document.getElementById('profile-cards');
    if (!profilesData.length) {
        container.innerHTML = '<div class="empty-state"><div class="empty-icon"></div><div class="empty-text">No profiles found</div></div>';
        return;
    }

    container.innerHTML = profilesData.slice(0, 12).map(p => {
        // Calculate risk_score from threat_score (they're the same)
        const riskScore = p.threat_score || 0;
        const riskColor = riskScore > 0.7 ? 'var(--red)' : riskScore > 0.4 ? 'var(--yellow)' : 'var(--green)';
        const riskLabel = riskScore > 0.7 ? 'HIGH RISK' : riskScore > 0.4 ? 'MEDIUM' : 'LOW';

        return `
            <div class="card" style="cursor:pointer" onclick="viewProfileDetail('${p.ip}')">
                <div class="card-body">
                    <div style="display:flex;justify-content:space-between;align-items:start;margin-bottom:12px">
                        <div class="mono" style="color:var(--cyan);font-size:0.9rem;font-weight:600">${p.ip}</div>
                        <span class="badge" style="background:${riskColor}20;color:${riskColor};border:1px solid ${riskColor}40">${riskLabel}</span>
                    </div>
                    <div style="font-size:0.7rem;color:var(--text-dim);margin-bottom:8px">
                        <div><strong>Attacks:</strong> ${p.attack_count}</div>
                        <div><strong>Types:</strong> ${(p.attack_types || []).slice(0, 2).join(', ')}</div>
                        <div><strong>Cluster:</strong> ${p.cluster_id !== null ? p.cluster_id : 'None'}</div>
                    </div>
                    <div style="font-size:0.65rem;color:var(--text-dim)">
                        Last seen: ${p.last_seen ? new Date(p.last_seen).toLocaleString() : 'Unknown'}
                    </div>
                </div>
        </div>
            `;
    }).join('');
}

async function viewProfileDetail(ip) {
    try {
        const resp = await fetch(`/api/attacker-profiles/${encodeURIComponent(ip)}`);
        const data = await resp.json();

        const riskScore = data.threat_score || 0;
        const types = (data.attack_types || []).join(', ') || 'Unknown';
        const cluster = data.cluster_id !== null ? `Cluster ${data.cluster_id}` : 'Unclassified';
        const firstSeen = data.first_seen ? new Date(data.first_seen).toLocaleString() : '—';
        const lastSeen = data.last_seen ? new Date(data.last_seen).toLocaleString() : '—';

        showToast(
            `Attacker: ${ip}\nRisk: ${(riskScore * 100).toFixed(0)}% | ${cluster}\nAttacks: ${data.attack_count || 0} | Types: ${types}\nFirst: ${firstSeen}\nLast:  ${lastSeen}`,
            riskScore > 0.7 ? 'error' : riskScore > 0.4 ? 'warning' : 'info',
            7000
        );
    } catch (e) {
        showToast('Failed to load profile details', 'error');
    }
}

async function exportProfiles(format) {
    try {
        const resp = await fetch(`/api/attacker-profiles/export?format=${format}`);
        const blob = await resp.blob();
        const url = window.URL.createObjectURL(blob);
        const a = document.createElement('a');
        a.href = url;
        a.download = `attacker_profiles_${new Date().toISOString().split('T')[0]}.${format}`;
        a.click();
    } catch (e) {
        showToast('Export failed', 'error');
    }
}

// Update loadPageData to include new pages
const originalLoadPageData = loadPageData;
loadPageData = async function (page) {
    if (page === 'attack-history') {
        await loadAttackHistory();
    } else if (page === 'attacker-profiles') {
        await loadAttackerProfiles();
    } else {
        await originalLoadPageData(page);
    }
};

// Update navigateTo titles
const titles = {
    overview: 'Command Overview',
    attacks: 'Attack Analysis',
    honeypots: 'Honeypot Management',
    'attack-history': 'Attack History',
    'attacker-profiles': 'Attacker Profiles',
    models: 'ML Detection Models',
    adaptive: 'Adaptive Learning Engine',
    sitelogs: 'Site Logs & Telemetry',
    blockchain: 'Blockchain Ledger',
    canary: 'Canary Tokens',
    fingerprints: 'Behavioral Fingerprints',
    settings: 'System Settings'
};

const originalNavigateTo = navigateTo;
navigateTo = function (page) {
    currentPage = page;
    document.querySelectorAll('.page-view').forEach(p => p.classList.remove('active'));
    document.querySelectorAll('.nav-item').forEach(n => n.classList.remove('active'));
    const target = document.getElementById('page-' + page);
    const nav = document.querySelector(`.nav-item[data-page="${page}"]`);
    if (target) target.classList.add('active');
    if (nav) nav.classList.add('active');
    document.getElementById('topbar-title').textContent = titles[page] || 'Dashboard';
    loadPageData(page);
};

// Add Wazuh title
titles['wazuh'] = 'Wazuh SIEM Integration';

// Extend loadPageData for Wazuh
const wazuhLoadPageData = loadPageData;
loadPageData = async function (page) {
    if (page === 'wazuh') {
        loadWazuhData();
    } else {
        await wazuhLoadPageData(page);
    }
};

async function loadWazuhData() {
    try {
        const [agentsRes, statsRes] = await Promise.all([
            fetch('/api/wazuh/agents'),
            fetch('/api/wazuh/manager-stats')
        ]);

        if (statsRes.ok) {
            const stats = await statsRes.json();
            if (stats.manager_info) {
                document.getElementById('wazuh-version').textContent = stats.manager_info.version || 'Connected';
            }
            if (stats.agents_summary) {
                document.getElementById('wazuh-active-agents').textContent = stats.agents_summary.active || '0';
                document.getElementById('wazuh-disconnected-agents').textContent = stats.agents_summary.disconnected || '0';
            }
            if (stats.manager_status) {
                const status = stats.manager_status;
                const isOnline = status.wazuh_modulesd === 'active' && status.wazuh_analysisd === 'active';
                document.getElementById('wazuh-manager-status').textContent = isOnline ? 'ONLINE' : 'DEGRADED';
                document.getElementById('wazuh-manager-status').style.color = isOnline ? 'var(--green)' : 'var(--yellow)';
            }
        }

        const tbody = document.getElementById('wazuh-agents-tbody');
        if (agentsRes.ok) {
            const data = await agentsRes.json();
            const agents = data.data?.affected_items || [];
            if (agents.length === 0) {
                tbody.innerHTML = `< tr > <td colspan="6" class="empty-state"><div class="empty-text">No agents found</div></td></tr > `;
                return;
            }
            tbody.innerHTML = agents.map(a => {
                const isAct = a.status === 'active';
                const statusHtml = `<span class="badge ${isAct ? 'badge-online' : 'badge-offline'}">${a.status.toUpperCase()}</span>`;
                return `<tr>
                    <td style="font-family:'JetBrains Mono',monospace">${a.id}</td>
                    <td>${a.name}</td>
                    <td>${a.ip || a.registerIP || 'N/A'}</td>
                    <td>${a.os ? a.os.name + ' ' + (a.os.version || '') : 'N/A'}</td>
                    <td>${a.version || 'N/A'}</td>
                    <td>${statusHtml}</td>
                </tr>`;
            }).join('');
        } else {
            tbody.innerHTML = `<tr><td colspan="6" class="empty-state" style="color:var(--red)"><div class="empty-text">Error loading agents from Wazuh API</div></td></tr>`;
        }
    } catch (e) {
        console.error('Error loading Wazuh data:', e);
    }
}

// SITE LOGS
// ═══════════════════════════════════════════════════════════

const SITES = ['banking', 'ecommerce', 'healthcare', 'blog', 'api_service', 'corporate', 'admin_panel'];
let currentSite = 'banking';
let currentSiteIsHp = false;
let currentSiteSubtab = 'traffic';

function initSiteLogs() {
    const tabsContainer = document.getElementById('site-logs-tabs');
    if (!tabsContainer) return;

    let html = '';

    // Single row of sites
    html += '<div style="display:flex;gap:8px;margin-bottom:16px;flex-wrap:wrap">';
    SITES.forEach(site => {
        html += `<button class="btn site-tab-btn" style="padding:8px 16px;font-size:0.8rem;background:var(--bg-card);color:var(--cyan);border:1px solid rgba(0,240,255,0.2)" onclick="selectSiteLog('${site}', false)" id="tab-${site}">${site.toUpperCase()}</button>`;
    });
    html += '</div>';

    // Real Site filter button (separate row)
    html += '<div style="margin-bottom:12px">';
    html += '<button class="btn filter-btn" id="filter-real" onclick="switchSiteType(false)" style="padding:8px 20px;font-size:0.8rem;background:rgba(0,240,255,0.2);color:var(--cyan);border:1px solid var(--cyan);font-weight:600">🌐 REAL SITE</button>';
    html += '</div>';

    // Honeypot filter button (separate row)
    html += '<div style="margin-bottom:16px">';
    html += '<button class="btn filter-btn" id="filter-hp" onclick="switchSiteType(true)" style="padding:8px 20px;font-size:0.8rem;background:var(--bg-card);color:var(--yellow);border:1px solid rgba(255,170,0,0.2);font-weight:600">🍯 HONEYPOT</button>';
    html += '</div>';

    tabsContainer.innerHTML = html;
    updateSiteTabsUI();
}

function switchSiteType(isHp) {
    currentSiteIsHp = isHp;
    updateSiteTabsUI();
    loadSiteLogsData();
}

function selectSiteLog(site, isHp) {
    currentSite = site;
    currentSiteIsHp = isHp;
    updateSiteTabsUI();
    loadSiteLogsData();
}

function updateSiteTabsUI() {
    // Update site tabs
    document.querySelectorAll('.site-tab-btn').forEach(b => {
        b.style.background = 'var(--bg-card)';
        b.style.color = 'var(--cyan)';
        b.style.border = '1px solid rgba(0,240,255,0.2)';
    });
    const activeTab = document.getElementById(`tab-${currentSite}`);
    if (activeTab) {
        activeTab.style.background = 'rgba(0,240,255,0.2)';
        activeTab.style.color = '#fff';
        activeTab.style.border = '1px solid var(--cyan)';
    }

    // Update filter buttons
    const realBtn = document.getElementById('filter-real');
    const hpBtn = document.getElementById('filter-hp');
    if (realBtn && hpBtn) {
        if (currentSiteIsHp) {
            realBtn.style.background = 'var(--bg-card)';
            realBtn.style.color = 'var(--cyan)';
            realBtn.style.border = '1px solid rgba(0,240,255,0.2)';
            hpBtn.style.background = 'rgba(255,170,0,0.2)';
            hpBtn.style.color = '#fff';
            hpBtn.style.border = '1px solid var(--yellow)';
        } else {
            realBtn.style.background = 'rgba(0,240,255,0.2)';
            realBtn.style.color = '#fff';
            realBtn.style.border = '1px solid var(--cyan)';
            hpBtn.style.background = 'var(--bg-card)';
            hpBtn.style.color = 'var(--yellow)';
            hpBtn.style.border = '1px solid rgba(255,170,0,0.2)';
        }
    }
}

function switchSiteSubtab(subtab) {
    currentSiteSubtab = subtab;
    document.querySelectorAll('.site-subtab').forEach(el => {
        el.classList.remove('active');
        el.style.color = 'var(--text-dim)';
        el.style.borderBottom = 'none';
    });
    const activeEl = document.querySelector(`.site-subtab[data-subtab="${subtab}"]`);
    if (activeEl) {
        activeEl.classList.add('active');
        activeEl.style.color = 'var(--cyan)';
        activeEl.style.borderBottom = '2px solid var(--cyan)';
    }

    document.querySelectorAll('.site-subtab-content').forEach(el => el.style.display = 'none');
    const contentEl = document.getElementById(`site-subtab-${subtab}`);
    if (contentEl) contentEl.style.display = 'block';

    loadSiteLogsData();
}

async function loadSiteLogsData() {
    if (currentSiteSubtab === 'traffic') await loadSiteTraffic();
    else if (currentSiteSubtab === 'attacks') await loadSiteAttacks();
    else if (currentSiteSubtab === 'stats') await loadSiteStats();
}

async function loadSiteTraffic() {
    const tbody = document.getElementById('site-logs-traffic-body');
    console.log('loadSiteTraffic called, tbody:', tbody);
    console.log('currentSite:', currentSite, 'currentSiteIsHp:', currentSiteIsHp);

    if (!tbody) {
        console.error('tbody not found!');
        return;
    }

    // Show loading state
    tbody.innerHTML = '<tr><td colspan="6" style="text-align:center;padding:20px;color:var(--cyan)">Loading traffic logs...</td></tr>';

    try {
        const url = `/api/adaptive/site-logs/${currentSite}?type=traffic&honeypot=${currentSiteIsHp}&limit=100`;
        console.log('Fetching:', url);
        const d = await fetch(url).then(r => r.json());
        console.log('Received data:', d);

        // Merge wazuh and attack logs, sort by timestamp DESC
        const combined = [...(d.wazuh_logs || []), ...(d.attack_logs || [])]
            .sort((a, b) => new Date(b.timestamp) - new Date(a.timestamp));

        console.log('Combined logs:', combined.length);

        if (!combined.length) {
            tbody.innerHTML = '<tr><td colspan="6" style="text-align:center;padding:20px;color:var(--text-dim)">No traffic logs found for this site</td></tr>';
            return;
        }

        let html = '';
        combined.forEach(log => {
            const time = log.timestamp ? log.timestamp.replace('T', ' ').slice(0, 19) : '—';
            const isWazuh = log.rule_id !== undefined;

            // Get IP - use actual IP if available, otherwise show agent/system
            let sourceIp = log.ip && log.ip.trim() ? log.ip : (isWazuh ? 'System' : '—');

            if (isWazuh) {
                // Wazuh log entry
                const levelColor = aleLevelColor(log.rule_level || 0);
                html += `<tr style="border-bottom:1px solid rgba(255,255,255,0.02);background:rgba(59,130,246,0.03)">
                    <td style="padding:8px;color:var(--text-dim);font-size:0.75rem">${time}</td>
                    <td style="padding:8px;color:var(--blue);font-weight:600;font-size:0.75rem">${sourceIp}</td>
                    <td style="padding:8px;color:var(--cyan);font-size:0.75rem">${log.agent_name || '—'}</td>
                    <td style="padding:8px;text-align:center;color:${levelColor};font-weight:700;font-size:0.75rem">L${log.rule_level || 0}</td>
                    <td style="padding:8px;color:var(--text-primary);font-size:0.75rem">${log.description || log.rule_description || '—'}</td>
                    <td style="padding:8px;color:var(--text-dim);font-size:0.7rem;font-family:monospace">${log.rule_id || '—'}</td>
                </tr>`;
            } else {
                // Attack/Proxy log entry
                html += `<tr style="border-bottom:1px solid rgba(255,255,255,0.02)">
                    <td style="padding:8px;color:var(--text-dim);font-size:0.75rem">${time}</td>
                    <td style="padding:8px;color:var(--yellow);font-weight:600;font-size:0.75rem">${sourceIp}</td>
                    <td style="padding:8px;color:var(--text-dim);font-size:0.75rem">Proxy</td>
                    <td style="padding:8px;text-align:center;color:var(--text-dim);font-size:0.75rem">—</td>
                    <td style="padding:8px;color:var(--text-primary);font-size:0.75rem">${log.method || ''} ${log.path || ''}</td>
                    <td style="padding:8px;color:var(--text-dim);font-size:0.7rem">${log.attack_type || 'Normal'}</td>
                </tr>`;
            }
        });
        tbody.innerHTML = html;
        console.log('Table updated with', combined.length, 'rows');
    } catch (e) {
        console.error('Error loading site traffic:', e);
        tbody.innerHTML = `<tr><td colspan="6" style="color:var(--red);text-align:center;padding:20px">Error loading data: ${e.message}</td></tr>`;
    }
}

async function loadSiteAttacks() {
    const tbody = document.getElementById('site-logs-attacks-body');
    if (!tbody) return;
    try {
        const d = await fetch(`/api/adaptive/site-logs/${currentSite}?type=attacks&honeypot=${currentSiteIsHp}&limit=50`).then(r => r.json());

        const combined = [...(d.attacks || []), ...(d.wazuh_attacks || [])]
            .sort((a, b) => new Date(b.timestamp) - new Date(a.timestamp));

        if (!combined.length) {
            tbody.innerHTML = '<tr><td colspan="5" style="text-align:center;padding:20px;color:var(--text-dim)">No attacks recorded</td></tr>';
            return;
        }

        let html = '';
        combined.forEach(log => {
            const time = log.timestamp ? log.timestamp.replace('T', ' ').slice(0, 19) : '—';
            const isWazuh = log.rule_id !== undefined;

            // Get IP - use actual IP if available, otherwise show System for Wazuh alerts
            let sourceIp = log.ip && log.ip.trim() ? log.ip : (isWazuh ? 'System' : '—');

            let threatType = isWazuh ? 'Wazuh Alert' : (log.attack_type || 'Unknown');
            let threatColor = isWazuh ? 'var(--blue)' : 'var(--red)';

            let sevText = isWazuh ? `Level ${log.rule_level}` : `${(log.confidence * 100).toFixed(0)}% Conf`;
            let sevColor = isWazuh ? aleLevelColor(log.rule_level) : 'var(--yellow)';

            let details = isWazuh ? log.rule_description : (log.payload || log.path);

            html += `<tr style="border-bottom:1px solid rgba(255,255,255,0.02);background:rgba(255,0,0,0.02)">
                <td style="padding:8px;color:var(--text-dim)">${time}</td>
                <td style="padding:8px;color:var(--cyan);font-weight:600">${sourceIp}</td>
                <td style="padding:8px;color:${threatColor}">${threatType}</td>
                <td style="padding:8px;text-align:center;color:${sevColor};font-weight:600">${sevText}</td>
                <td style="padding:8px;font-family:monospace;color:var(--text-dim);font-size:0.65rem;word-break:break-all">${details}</td>
            </tr>`;
        });
        tbody.innerHTML = html;
    } catch (e) {
        tbody.innerHTML = `<tr><td colspan="5" style="color:var(--red);text-align:center">Error loading data</td></tr>`;
    }
}

async function loadSiteStats() {
    try {
        const d = await fetch(`/api/adaptive/site-logs/${currentSite}?type=stats&honeypot=${currentSiteIsHp}`).then(r => r.json());

        document.getElementById('site-stat-total').textContent = (d.total_events || 0).toLocaleString();

        const typesContainer = document.getElementById('site-stat-types');
        if (d.by_type && d.by_type.length) {
            typesContainer.innerHTML = d.by_type.map(t =>
                `<div style="display:flex;justify-content:space-between;margin-bottom:4px;padding-bottom:4px;border-bottom:1px solid rgba(255,255,255,0.05)">
                    <span style="color:var(--text-dim)">${t.attack_type || 'Unknown'}</span>
                    <strong style="color:var(--cyan)">${t.n}</strong>
                </div>`
            ).join('');
        } else {
            typesContainer.innerHTML = '<div style="color:var(--text-dim)">No attack types recorded</div>';
        }

        const sevContainer = document.getElementById('site-stat-severity');
        if (d.by_severity && d.by_severity.length) {
            const max = Math.max(...d.by_severity.map(s => s.n));
            sevContainer.innerHTML = d.by_severity.map(s => {
                const height = max > 0 ? (s.n / max) * 100 : 0;
                return `<div style="flex:1;display:flex;flex-direction:column;align-items:center;gap:4px">
                    <div style="font-size:0.6rem;color:var(--text-dim)">${s.n}</div>
                    <div style="width:100%;background:${aleLevelColor(s.rule_level)};height:${height}px;border-radius:2px 2px 0 0;min-height:2px"></div>
                    <div style="font-size:0.65rem;color:var(--text-primary)">L${s.rule_level}</div>
                </div>`;
            }).join('');
        } else {
            sevContainer.innerHTML = '<div style="color:var(--text-dim);width:100%;text-align:center;align-self:center">No Wazuh alerts recorded</div>';
        }

    } catch (e) { }
}

