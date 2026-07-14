/**
 * DeceptiCloud — Behavioral Fingerprint Collector
 * 
 * Collects behavioral telemetry from attacker interactions on HONEYPOT pages only.
 * This script is NEVER loaded on real sites.
 * 
 * Collects:
 *   - Keystroke timing patterns (inter-key intervals in ms)
 *   - Mouse movement dynamics (position, velocity, acceleration)
 *   - Browser fingerprint (canvas, WebGL, screen, timezone, fonts)
 *   - Scroll behavior and page interaction metrics
 *   - Time-on-page and form interaction counts
 * 
 * Data is sent to /api/fingerprint endpoint every 10 seconds.
 */

(function () {
    'use strict';

    // STATE

    const state = {
        keystrokeIntervals: [],
        lastKeystrokeTime: null,
        mouseMovements: [],
        mouseSampleCount: 0,
        scrollDepth: 0,
        formInteractions: 0,
        pageLoadTime: Date.now(),
        pagesVisited: [window.location.pathname],
        requestIntervals: [],
        lastRequestTime: Date.now(),
    };

    // KEYSTROKE TRACKING

    document.addEventListener('keydown', function (e) {
        const now = Date.now();
        if (state.lastKeystrokeTime !== null) {
            const interval = now - state.lastKeystrokeTime;
            if (interval < 5000) { // ignore pauses > 5s
                state.keystrokeIntervals.push(interval);
            }
        }
        state.lastKeystrokeTime = now;
    });

    // MOUSE MOVEMENT TRACKING (sampled every 50ms max)

    let lastMouseSample = 0;
    document.addEventListener('mousemove', function (e) {
        const now = Date.now();
        if (now - lastMouseSample < 50) return; // throttle to 20Hz
        lastMouseSample = now;

        state.mouseMovements.push({
            x: e.clientX,
            y: e.clientY,
            t: now,
        });

        // Keep only last 200 samples to avoid memory bloat

        if (state.mouseMovements.length > 200) {
            state.mouseMovements = state.mouseMovements.slice(-200);
        }
        state.mouseSampleCount++;
    });

    // SCROLL TRACKING

    document.addEventListener('scroll', function () {
        const scrollTop = window.pageYOffset || document.documentElement.scrollTop;
        const docHeight = document.documentElement.scrollHeight - window.innerHeight;
        if (docHeight > 0) {
            const depth = Math.round((scrollTop / docHeight) * 100);
            if (depth > state.scrollDepth) {
                state.scrollDepth = depth;
            }
        }
    });

    // FORM INTERACTION TRACKING

    document.addEventListener('focus', function (e) {
        if (['INPUT', 'TEXTAREA', 'SELECT'].includes(e.target.tagName)) {
            state.formInteractions++;
        }
    }, true);

    // BROWSER FINGERPRINTING

    function getCanvasHash() {
        try {
            const canvas = document.createElement('canvas');
            canvas.width = 200;
            canvas.height = 50;
            const ctx = canvas.getContext('2d');

            ctx.textBaseline = 'top';
            ctx.font = '14px Arial';
            ctx.fillStyle = '#f60';
            ctx.fillRect(125, 1, 62, 20);
            ctx.fillStyle = '#069';
            ctx.fillText('DeceptiCloud FP', 2, 15);
            ctx.fillStyle = 'rgba(102, 204, 0, 0.7)';
            ctx.fillText('DeceptiCloud FP', 4, 17);

            return hashString(canvas.toDataURL());
        } catch (e) {
            return 'canvas_unavailable';
        }
    }

    function getWebGLHash() {
        try {
            const canvas = document.createElement('canvas');
            const gl = canvas.getContext('webgl') || canvas.getContext('experimental-webgl');
            if (!gl) return 'webgl_unavailable';

            const debugInfo = gl.getExtension('WEBGL_debug_renderer_info');
            const vendor = debugInfo ? gl.getParameter(debugInfo.UNMASKED_VENDOR_WEBGL) : '';
            const renderer = debugInfo ? gl.getParameter(debugInfo.UNMASKED_RENDERER_WEBGL) : '';

            return hashString(vendor + '|' + renderer);
        } catch (e) {
            return 'webgl_unavailable';
        }
    }

    function getFontsHash() {
        const testFonts = [
            'Arial', 'Verdana', 'Times New Roman', 'Courier New',
            'Georgia', 'Palatino', 'Garamond', 'Comic Sans MS',
            'Impact', 'Lucida Console', 'Tahoma', 'Trebuchet MS',
        ];

        const available = [];
        const testString = 'mmmmmmmmmmlli';
        const testSize = '72px';
        const baseFonts = ['monospace', 'sans-serif', 'serif'];

        const span = document.createElement('span');
        span.style.position = 'absolute';
        span.style.left = '-9999px';
        span.style.fontSize = testSize;
        span.textContent = testString;
        document.body.appendChild(span);

        const baseWidths = {};
        for (const baseFont of baseFonts) {
            span.style.fontFamily = baseFont;
            baseWidths[baseFont] = span.offsetWidth;
        }

        for (const font of testFonts) {
            for (const baseFont of baseFonts) {
                span.style.fontFamily = "'" + font + "', " + baseFont;
                if (span.offsetWidth !== baseWidths[baseFont]) {
                    available.push(font);
                    break;
                }
            }
        }

        document.body.removeChild(span);
        return hashString(available.join(','));
    }

    function hashString(str) {
        let hash = 0;
        for (let i = 0; i < str.length; i++) {
            const char = str.charCodeAt(i);
            hash = ((hash << 5) - hash) + char;
            hash = hash & hash; // Convert to 32bit integer
        }
        return Math.abs(hash).toString(16).padStart(8, '0');
    }

    // SEND FINGERPRINT DATA

    function collectAndSend() {
        const now = Date.now();

        // Track request intervals

        state.requestIntervals.push(now - state.lastRequestTime);
        state.lastRequestTime = now;

        const payload = {
            // Browser fingerprint

            canvas_hash: getCanvasHash(),
            webgl_hash: getWebGLHash(),
            fonts_hash: getFontsHash(),
            screen: {
                resolution: screen.width + 'x' + screen.height,
                colorDepth: screen.colorDepth,
                availWidth: screen.availWidth,
                availHeight: screen.availHeight,
            },
            timezone_offset: new Date().getTimezoneOffset(),
            language: navigator.language || navigator.userLanguage,
            platform: navigator.platform,
            touch_support: 'ontouchstart' in window || navigator.maxTouchPoints > 0,
            do_not_track: navigator.doNotTrack,
            plugins_count: navigator.plugins ? navigator.plugins.length : 0,

            // Behavioral data

            keystroke_intervals: state.keystrokeIntervals.slice(-50),
            mouse_movements: state.mouseMovements.slice(-100),
            scroll_depth: state.scrollDepth,
            form_interactions: state.formInteractions,
            time_on_page: Math.round((now - state.pageLoadTime) / 1000),
            pages_visited: state.pagesVisited,
            request_intervals: state.requestIntervals.slice(-20),
        };

        // Send as beacon (non-blocking)

        try {
            const blob = new Blob([JSON.stringify(payload)], { type: 'application/json' });
            navigator.sendBeacon('/api/fingerprint', blob);
        } catch (e) {
            // Fallback to fetch

            fetch('/api/fingerprint', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify(payload),
                keepalive: true,
            }).catch(function () { });
        }

        // Reset some counters after sending

        state.keystrokeIntervals = [];
        state.mouseMovements = [];
    }

    // SCHEDULE SENDING

    // Send first fingerprint after 5 seconds, then every 15 seconds

    setTimeout(collectAndSend, 5000);
    setInterval(collectAndSend, 15000);

    // Also send on page unload

    window.addEventListener('beforeunload', collectAndSend);

})();
