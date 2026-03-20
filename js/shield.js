/* ============================================================
   YOGA SCHWEIZ — Fortress Shield v2
   Advanced multi-layer anti-scraping protection system
   ============================================================ */

(function () {
    'use strict';

    var SHIELD = {
        score: 0,        // Bot probability score (0-100)
        checks: [],       // Failed checks log
        blocked: false,
        humanVerified: false
    };

    // ================================================================
    // LAYER 1: Deep Bot Detection (50+ signatures)
    // ================================================================
    var ua = navigator.userAgent || '';
    var botUA = [
        /bot/i, /crawl/i, /spider/i, /scrape/i, /fetch/i, /wget/i, /curl/i,
        /python/i, /java\//i, /perl/i, /ruby/i, /php\//i, /go-http/i, /node-fetch/i,
        /okhttp/i, /axios/i, /httpie/i, /postman/i, /insomnia/i, /thunder/i,
        /scrapy/i, /selenium/i, /phantomjs/i, /puppeteer/i, /playwright/i,
        /headless/i, /lighthouse/i, /httrack/i, /offline/i, /archiver/i,
        /gptbot/i, /chatgpt/i, /ccbot/i, /anthropic/i, /bytespider/i, /claude/i,
        /semrush/i, /ahrefs/i, /mj12bot/i, /dotbot/i, /dataforseo/i, /megaindex/i,
        /blexbot/i, /rogerbot/i, /seznambot/i, /sogou/i, /baidu/i, /yandexbot/i,
        /petal/i, /applebot/i, /facebookexternalhit/i, /twitterbot/i,
        /slackbot/i, /telegrambot/i, /whatsapp/i, /discord/i,
        /libwww/i, /apache-http/i, /colly/i, /goutte/i
    ];
    for (var i = 0; i < botUA.length; i++) {
        if (botUA[i].test(ua)) { SHIELD.score += 60; SHIELD.checks.push('ua:' + botUA[i]); break; }
    }

    // ================================================================
    // LAYER 2: Headless Browser Detection (20+ signals)
    // ================================================================
    // webdriver flag
    if (navigator.webdriver) { SHIELD.score += 40; SHIELD.checks.push('webdriver'); }

    // Missing plugins (headless browsers have 0)
    if (navigator.plugins && navigator.plugins.length === 0 && !/Mobile|Android|iPhone|iPad/i.test(ua)) {
        SHIELD.score += 15; SHIELD.checks.push('no-plugins');
    }

    // Missing languages
    if (!navigator.languages || navigator.languages.length === 0) {
        SHIELD.score += 20; SHIELD.checks.push('no-languages');
    }

    // Chrome without chrome object
    if (/Chrome/.test(ua) && !window.chrome) {
        SHIELD.score += 25; SHIELD.checks.push('fake-chrome');
    }

    // Permissions API anomaly
    if (navigator.permissions) {
        navigator.permissions.query({ name: 'notifications' }).then(function (r) {
            if (r.state === 'prompt' && Notification.permission === 'denied') {
                SHIELD.score += 20; SHIELD.checks.push('perm-anomaly');
            }
        }).catch(function () {});
    }

    // Automation-related properties
    var autoProps = ['__webdriver_evaluate', '__selenium_evaluate', '__fxdriver_evaluate',
        '__driver_unwrapped', '__webdriver_unwrapped', '__driver_evaluate',
        '__selenium_unwrapped', '__fxdriver_unwrapped', '_phantom', '__nightmare',
        '_selenium', 'callPhantom', 'callSelenium', '_Recaptcha'];
    for (var ap = 0; ap < autoProps.length; ap++) {
        if (window[autoProps[ap]] !== undefined) {
            SHIELD.score += 30; SHIELD.checks.push('auto-prop:' + autoProps[ap]); break;
        }
    }

    // Check for overridden toString (common in automation)
    try {
        if (navigator.toString() !== '[object Navigator]') {
            SHIELD.score += 15; SHIELD.checks.push('nav-tostring');
        }
    } catch (e) {}

    // ================================================================
    // LAYER 3: Canvas Fingerprint Verification
    // ================================================================
    try {
        var canvas = document.createElement('canvas');
        canvas.width = 200; canvas.height = 50;
        var ctx = canvas.getContext('2d');
        ctx.textBaseline = 'top';
        ctx.font = '14px Arial';
        ctx.fillStyle = '#f60';
        ctx.fillRect(0, 0, 200, 50);
        ctx.fillStyle = '#069';
        ctx.fillText('YogaSchweiz\ud83e\uddd8', 2, 15);
        var dataUrl = canvas.toDataURL();
        // Headless browsers often return identical/empty canvas
        if (dataUrl.length < 1000) {
            SHIELD.score += 20; SHIELD.checks.push('canvas-empty');
        }
    } catch (e) {
        SHIELD.score += 10; SHIELD.checks.push('canvas-error');
    }

    // ================================================================
    // LAYER 4: WebGL Detection
    // ================================================================
    try {
        var glCanvas = document.createElement('canvas');
        var gl = glCanvas.getContext('webgl') || glCanvas.getContext('experimental-webgl');
        if (!gl) {
            SHIELD.score += 15; SHIELD.checks.push('no-webgl');
        } else {
            var debugInfo = gl.getExtension('WEBGL_debug_renderer_info');
            if (debugInfo) {
                var renderer = gl.getParameter(debugInfo.UNMASKED_RENDERER_WEBGL);
                if (/SwiftShader|llvmpipe|Mesa/i.test(renderer)) {
                    SHIELD.score += 25; SHIELD.checks.push('webgl-software:' + renderer);
                }
            }
        }
    } catch (e) {}

    // ================================================================
    // LAYER 5: Timing Analysis
    // ================================================================
    var loadTime = Date.now();
    // Bots load and parse instantly, humans take time
    setTimeout(function () {
        if (!SHIELD.humanVerified && SHIELD.score >= 30) {
            // Still suspicious after 2 seconds with no human interaction
            SHIELD.score += 10;
        }
    }, 2000);

    // ================================================================
    // LAYER 6: If score >= 50, BLOCK and serve decoy
    // ================================================================
    if (SHIELD.score >= 50) {
        SHIELD.blocked = true;
        // Override XHR to serve empty data
        var origOpen = XMLHttpRequest.prototype.open;
        XMLHttpRequest.prototype.open = function (m, url) {
            if (typeof url === 'string' && (url.indexOf('.enc.json') !== -1 || url.indexOf('studios') !== -1)) {
                arguments[1] = 'data:application/json,' + encodeURIComponent('{"v":1,"d":"blocked"}');
            }
            return origOpen.apply(this, arguments);
        };
        console.log('%c\u26D4 Access blocked. Automated access detected.', 'color:red;font-size:16px;font-weight:bold;');
        return;
    }

    // ================================================================
    // LAYER 7: Human Behavior Verification
    // ================================================================
    var humanSignals = { mouse: 0, scroll: 0, touch: 0, key: 0 };

    document.addEventListener('mousemove', function () {
        humanSignals.mouse++;
        if (humanSignals.mouse > 3) SHIELD.humanVerified = true;
    }, { passive: true });

    document.addEventListener('scroll', function () {
        humanSignals.scroll++;
        if (humanSignals.scroll > 2) SHIELD.humanVerified = true;
    }, { passive: true });

    document.addEventListener('touchstart', function () {
        humanSignals.touch++;
        SHIELD.humanVerified = true;
    }, { passive: true });

    document.addEventListener('keydown', function () {
        humanSignals.key++;
        SHIELD.humanVerified = true;
    }, { passive: true });

    // ================================================================
    // LAYER 8: Anti-Copy & Anti-Inspect
    // ================================================================
    // Right-click
    document.addEventListener('contextmenu', function (e) {
        if (e.target.tagName === 'INPUT' || e.target.tagName === 'TEXTAREA') return;
        e.preventDefault();
    });

    // Selection
    document.addEventListener('selectstart', function (e) {
        var tag = e.target.tagName;
        if (tag === 'INPUT' || tag === 'TEXTAREA' || tag === 'SELECT') return;
        if (e.target.closest && (e.target.closest('.guide-content') || e.target.closest('.faq-answer'))) return;
        e.preventDefault();
    });

    // Keyboard shortcuts
    document.addEventListener('keydown', function (e) {
        if (e.target.tagName === 'INPUT' || e.target.tagName === 'TEXTAREA') return;
        var blocked = false;
        if (e.ctrlKey || e.metaKey) {
            if (['u', 'U', 's', 'S'].indexOf(e.key) !== -1) blocked = true;
            if (e.shiftKey && ['I', 'i', 'J', 'j', 'C', 'c'].indexOf(e.key) !== -1) blocked = true;
        }
        if (e.key === 'F12') blocked = true;
        if (blocked) e.preventDefault();
    });

    // Drag
    document.addEventListener('dragstart', function (e) { e.preventDefault(); });

    // ================================================================
    // LAYER 9: Anti-DevTools Detection
    // ================================================================
    var devToolsOpen = false;

    // Method 1: debugger timing
    setInterval(function () {
        var t1 = performance.now();
        // debugger statement slows down execution when DevTools is open
        // We use a more subtle approach: element inspection detection
        var el = document.createElement('div');
        Object.defineProperty(el, 'id', {
            get: function () {
                devToolsOpen = true;
            }
        });
        // This triggers the getter only when DevTools inspects the element
        console.debug(el);
    }, 3000);

    // Method 2: window size difference (DevTools changes inner dimensions)
    var checkDevTools = function () {
        var widthThreshold = window.outerWidth - window.innerWidth > 160;
        var heightThreshold = window.outerHeight - window.innerHeight > 160;
        if (widthThreshold || heightThreshold) {
            devToolsOpen = true;
        }
    };
    window.addEventListener('resize', checkDevTools);
    checkDevTools();

    // ================================================================
    // LAYER 10: Anti-Iframe (Clickjacking)
    // ================================================================
    if (window.top !== window.self) {
        try { window.top.location = window.self.location; } catch (e) {
            document.body.innerHTML = '<p style="padding:40px;text-align:center;font-size:18px;">This site cannot be displayed in a frame.</p>';
            return;
        }
    }

    // ================================================================
    // LAYER 11: Honeypot Traps (multiple)
    // ================================================================
    var honeypots = [
        { href: '/api/v1/studios', text: 'API endpoint' },
        { href: '/data/export.json', text: 'export data' },
        { href: '/admin/database', text: 'admin panel' },
        { href: '/sitemap-studios.xml', text: 'studio sitemap' }
    ];
    for (var h = 0; h < honeypots.length; h++) {
        var hp = document.createElement('a');
        hp.href = honeypots[h].href;
        hp.textContent = honeypots[h].text;
        hp.style.cssText = 'position:absolute;left:-9999px;top:-9999px;opacity:0;height:1px;width:1px;overflow:hidden;pointer-events:none;';
        hp.setAttribute('aria-hidden', 'true');
        hp.setAttribute('tabindex', '-1');
        document.body.appendChild(hp);
    }

    // ================================================================
    // LAYER 12: Request Rate Limiter (Advanced)
    // ================================================================
    var reqLog = [];
    var origFetch = window.fetch;
    if (origFetch) {
        window.fetch = function () {
            var now = Date.now();
            reqLog.push(now);
            // Clean old entries
            while (reqLog.length > 0 && now - reqLog[0] > 10000) reqLog.shift();
            // More than 50 requests in 10 seconds
            if (reqLog.length > 50) {
                SHIELD.blocked = true;
                return Promise.reject(new Error('Rate limited'));
            }
            return origFetch.apply(this, arguments);
        };
    }

    // Also monitor XHR
    var xhrCount = 0;
    var xhrWindow = Date.now();
    var origXHROpen = XMLHttpRequest.prototype.open;
    XMLHttpRequest.prototype.open = function () {
        xhrCount++;
        var now = Date.now();
        if (now - xhrWindow > 10000) { xhrCount = 1; xhrWindow = now; }
        if (xhrCount > 50) {
            arguments[1] = 'data:application/json,{"error":"rate limited"}';
        }
        return origXHROpen.apply(this, arguments);
    };

    // ================================================================
    // LAYER 13: Content Watermarking (Advanced)
    // ================================================================
    var wmChars = ['\u200B', '\u200C', '\u200D', '\uFEFF', '\u200E', '\u200F', '\u2060', '\u2061'];

    function watermark(text) {
        if (!text || text.length < 5) return text;
        // Generate unique watermark pattern based on session
        var session = Date.now().toString(36);
        var result = '';
        for (var i = 0; i < text.length; i++) {
            result += text[i];
            if (i > 0 && i % 15 === 0) {
                // Encode session info in watermark pattern
                var charIdx = (session.charCodeAt(i % session.length) + i) % wmChars.length;
                result += wmChars[charIdx];
            }
        }
        return result;
    }

    // Watch for new studio cards and watermark them
    var wmObserver = new MutationObserver(function (mutations) {
        for (var m = 0; m < mutations.length; m++) {
            var nodes = mutations[m].addedNodes;
            for (var n = 0; n < nodes.length; n++) {
                if (nodes[n].nodeType !== 1) continue;
                var targets = nodes[n].querySelectorAll ? nodes[n].querySelectorAll('.studio-name, .studio-description, .studio-address span, .schedule-class, .schedule-studio') : [];
                for (var t = 0; t < targets.length; t++) {
                    if (!targets[t].dataset.wm) {
                        targets[t].textContent = watermark(targets[t].textContent);
                        targets[t].dataset.wm = '1';
                    }
                }
            }
        }
    });
    wmObserver.observe(document.body, { childList: true, subtree: true });

    // ================================================================
    // LAYER 14: Proof of Work (computational challenge)
    // ================================================================
    // Before data loads, browser must solve a small challenge
    // This slows down automated bulk scraping
    window._yogaProofOfWork = function () {
        var challenge = Date.now().toString();
        var nonce = 0;
        // Find a nonce where hash starts with '00' (trivial for single page, costly at scale)
        while (nonce < 100000) {
            var input = challenge + nonce;
            var hash = 0;
            for (var i = 0; i < input.length; i++) {
                hash = ((hash << 5) - hash) + input.charCodeAt(i);
                hash |= 0;
            }
            if ((hash & 0xFF) === 0) return nonce; // Found
            nonce++;
        }
        return nonce;
    };
    // Execute proof of work
    window._yogaProofOfWork();

    // ================================================================
    // LAYER 15: DOM Mutation Trap
    // ================================================================
    // Detect if someone is programmatically reading all DOM elements
    var domReadCount = 0;
    var origGetElementById = document.getElementById;
    document.getElementById = function (id) {
        domReadCount++;
        if (domReadCount > 500 && !SHIELD.humanVerified) {
            // Excessive DOM reads without human interaction = bot
            SHIELD.score += 30;
        }
        return origGetElementById.call(document, id);
    };

    // ================================================================
    // LAYER 16: Clipboard Poisoning
    // ================================================================
    document.addEventListener('copy', function (e) {
        if (e.target.tagName === 'INPUT' || e.target.tagName === 'TEXTAREA') return;
        var selection = window.getSelection();
        if (!selection || selection.toString().length < 20) return;

        // Append source attribution to any copied text
        var copiedText = selection.toString();
        var attribution = '\n\n[Quelle: yogaschweiz | Kopieren und Weiterverbreiten ohne Genehmigung untersagt]';
        e.preventDefault();
        if (e.clipboardData) {
            e.clipboardData.setData('text/plain', copiedText + attribution);
        }
    });

    // ================================================================
    // LAYER 17: Decoy Data Nodes
    // ================================================================
    // Insert invisible fake data to confuse scrapers that parse the DOM
    var decoyStudios = [
        'Phantom Yoga Studio', 'Ghost Flow Center', 'Invisible Shala',
        'Decoy Yoga House', 'Trap Yoga Lab', 'Fake Zen Studio'
    ];
    var decoyContainer = document.createElement('div');
    decoyContainer.style.cssText = 'position:absolute;left:-99999px;top:-99999px;width:1px;height:1px;overflow:hidden;opacity:0;pointer-events:none;';
    decoyContainer.setAttribute('aria-hidden', 'true');
    for (var d = 0; d < decoyStudios.length; d++) {
        var decoy = document.createElement('div');
        decoy.className = 'studio-card';
        decoy.innerHTML = '<h3 class="studio-name">' + decoyStudios[d] + '</h3>' +
            '<p class="studio-address">Fake Street ' + (d + 1) + ', 0000 Nowhere</p>' +
            '<p class="studio-description">This is decoy data. If you see this, your scraper is collecting fake data.</p>';
        decoyContainer.appendChild(decoy);
    }
    document.body.appendChild(decoyContainer);

    // ================================================================
    // LAYER 18: Print Protection
    // ================================================================
    window.addEventListener('beforeprint', function () {
        // Replace content when trying to print
        var cards = document.querySelectorAll('.studio-card .studio-name');
        for (var p = 0; p < cards.length; p++) {
            cards[p].dataset.origText = cards[p].textContent;
            cards[p].textContent = '[Print protected - visit yogaschweiz online]';
        }
    });
    window.addEventListener('afterprint', function () {
        var cards = document.querySelectorAll('.studio-card .studio-name');
        for (var p = 0; p < cards.length; p++) {
            if (cards[p].dataset.origText) {
                cards[p].textContent = cards[p].dataset.origText;
                delete cards[p].dataset.origText;
            }
        }
    });

    // ================================================================
    // LAYER 19: CSS-Based Protection
    // ================================================================
    // Inject CSS that makes printed/saved versions useless
    var antiPrintCSS = document.createElement('style');
    antiPrintCSS.textContent =
        '@media print { .studio-card, .schedule-row, .guide-comparison-table { display: none !important; } ' +
        'body::after { content: "Drucken nicht erlaubt. Besuche yogaschweiz online."; display: block; padding: 40px; text-align: center; font-size: 20px; } }' +
        '.studio-name, .studio-description { -webkit-print-color-adjust: exact; }';
    document.head.appendChild(antiPrintCSS);

    // ================================================================
    // LAYER 20: Console Warning (intimidation)
    // ================================================================
    console.log('%c\u26A0\uFE0F STOP!', 'color:red;font-size:60px;font-weight:bold;text-shadow:2px 2px 4px rgba(0,0,0,0.3);');
    console.log('%cDiese Website ist durch ein mehrstufiges Sicherheitssystem geschützt.\nAlle Daten sind verschlüsselt und mit unsichtbaren Wasserzeichen versehen.\nAutomatisiertes Scraping wird erkannt, protokolliert und blockiert.\n\nThis website is protected by a multi-layer security system.\nAll data is encrypted and invisibly watermarked.\nAutomated scraping is detected, logged and blocked.', 'color:#333;font-size:13px;line-height:1.8;');
    console.log('%c\u00A9 YogaSchweiz — Alle Rechte vorbehalten', 'color:#6B5B95;font-size:12px;font-weight:bold;');

})();
