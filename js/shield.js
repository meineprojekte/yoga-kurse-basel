/* ============================================================
   YOGA SCHWEIZ — Anti-Scraping Shield
   Multi-layer protection against bots, scrapers, and data theft.
   GDPR-compliant: no personal data collected.
   ============================================================ */

(function () {
    'use strict';

    // ===== LAYER 1: Bot Detection via User-Agent =====
    var botPatterns = [
        /bot/i, /crawl/i, /spider/i, /scrape/i, /fetch/i, /wget/i, /curl/i,
        /python/i, /java\//i, /perl/i, /ruby/i, /php/i, /go-http/i, /node-fetch/i,
        /okhttp/i, /axios/i, /request/i, /httpie/i, /postman/i, /insomnia/i,
        /scrapy/i, /selenium/i, /phantomjs/i, /puppeteer/i, /playwright/i,
        /headless/i, /chrome-lighthouse/i, /httrack/i, /offline/i, /archiver/i,
        /gptbot/i, /chatgpt/i, /ccbot/i, /anthropic/i, /bytespider/i,
        /semrush/i, /ahrefs/i, /mj12bot/i, /dotbot/i, /dataforseo/i,
        /screaming.frog/i, /megaindex/i, /blexbot/i
    ];

    var ua = navigator.userAgent || '';
    var isBot = false;
    for (var i = 0; i < botPatterns.length; i++) {
        if (botPatterns[i].test(ua)) { isBot = true; break; }
    }

    // ===== LAYER 2: Headless Browser Detection =====
    var isHeadless = (
        navigator.webdriver === true ||
        !window.chrome && /Chrome/.test(ua) ||
        navigator.languages === undefined ||
        (navigator.languages && navigator.languages.length === 0) ||
        navigator.plugins.length === 0 && !/Mobile|Android/.test(ua)
    );

    // ===== LAYER 3: If bot detected, serve decoy data =====
    if (isBot || isHeadless) {
        // Override fetch/XHR to return empty data for bots
        var origXHROpen = XMLHttpRequest.prototype.open;
        XMLHttpRequest.prototype.open = function (method, url) {
            if (typeof url === 'string' && url.indexOf('studios_') !== -1) {
                // Redirect to decoy
                arguments[1] = 'data:application/json,{"studios":[],"note":"Access restricted"}';
            }
            return origXHROpen.apply(this, arguments);
        };
        console.log('%cAccess restricted for automated tools.', 'color:red;font-size:20px;');
        return; // Stop executing further protections
    }

    // ===== LAYER 4: Anti-Copy Protection =====
    // Disable right-click context menu
    document.addEventListener('contextmenu', function (e) {
        // Allow on input/textarea for usability
        if (e.target.tagName === 'INPUT' || e.target.tagName === 'TEXTAREA') return;
        e.preventDefault();
    });

    // Disable text selection on studio data (but allow on search/form fields)
    document.addEventListener('selectstart', function (e) {
        var tag = e.target.tagName;
        if (tag === 'INPUT' || tag === 'TEXTAREA' || tag === 'SELECT') return;
        // Allow selection in guide/FAQ sections for usability
        if (e.target.closest && (e.target.closest('.guide-content') || e.target.closest('.faq-answer'))) return;
        e.preventDefault();
    });

    // Disable common copy shortcuts (Ctrl+C, Ctrl+U, Ctrl+S, Ctrl+A)
    document.addEventListener('keydown', function (e) {
        // Allow in input fields
        if (e.target.tagName === 'INPUT' || e.target.tagName === 'TEXTAREA') return;

        if (e.ctrlKey || e.metaKey) {
            // Block: Ctrl+U (view source), Ctrl+S (save page), Ctrl+A (select all)
            if (e.key === 'u' || e.key === 'U' || e.key === 's' || e.key === 'S') {
                e.preventDefault();
            }
            // Block Ctrl+Shift+I (DevTools), Ctrl+Shift+J (Console), Ctrl+Shift+C (Inspector)
            if (e.shiftKey && (e.key === 'I' || e.key === 'i' || e.key === 'J' || e.key === 'j' || e.key === 'C' || e.key === 'c')) {
                e.preventDefault();
            }
        }
        // Block F12
        if (e.key === 'F12') {
            e.preventDefault();
        }
    });

    // Disable drag of images/content
    document.addEventListener('dragstart', function (e) {
        e.preventDefault();
    });

    // ===== LAYER 5: Anti-Iframe (Clickjacking Prevention) =====
    if (window.top !== window.self) {
        // Site is being loaded in an iframe — break out
        try { window.top.location = window.self.location; } catch (e) {
            // Can't break out (cross-origin), hide content
            document.body.innerHTML = '<p style="padding:40px;text-align:center;">This site cannot be displayed in a frame.</p>';
        }
    }

    // ===== LAYER 6: Honeypot Trap =====
    // Invisible link that only bots will follow
    var honeypot = document.createElement('a');
    honeypot.href = '/trap-do-not-follow';
    honeypot.textContent = 'important data';
    honeypot.style.cssText = 'position:absolute;left:-9999px;top:-9999px;opacity:0;height:1px;width:1px;overflow:hidden;';
    honeypot.setAttribute('aria-hidden', 'true');
    honeypot.setAttribute('tabindex', '-1');
    document.body.appendChild(honeypot);

    // ===== LAYER 7: Request Rate Monitoring =====
    // Detect rapid-fire requests (sign of scraping)
    var requestCount = 0;
    var requestWindow = Date.now();
    var origFetch = window.fetch;
    if (origFetch) {
        window.fetch = function () {
            requestCount++;
            var now = Date.now();
            if (now - requestWindow < 5000 && requestCount > 30) {
                // More than 30 requests in 5 seconds = likely bot
                console.warn('Rate limit triggered');
                return Promise.reject(new Error('Rate limited'));
            }
            if (now - requestWindow > 5000) {
                requestCount = 0;
                requestWindow = now;
            }
            return origFetch.apply(this, arguments);
        };
    }

    // ===== LAYER 8: Content Watermarking =====
    // Add invisible zero-width characters to text content
    // These act as a fingerprint if someone copies the data
    var watermarkChars = ['\u200B', '\u200C', '\u200D', '\uFEFF']; // zero-width space, non-joiner, joiner, BOM

    function addWatermark(text) {
        if (!text || text.length < 10) return text;
        // Insert watermark every ~20 characters
        var result = '';
        for (var i = 0; i < text.length; i++) {
            result += text[i];
            if (i > 0 && i % 20 === 0) {
                result += watermarkChars[i % watermarkChars.length];
            }
        }
        return result;
    }

    // Apply watermark to studio cards after they render
    var observer = new MutationObserver(function (mutations) {
        for (var m = 0; m < mutations.length; m++) {
            var added = mutations[m].addedNodes;
            for (var n = 0; n < added.length; n++) {
                if (added[n].nodeType !== 1) continue;
                // Watermark studio names and descriptions
                var names = added[n].querySelectorAll ? added[n].querySelectorAll('.studio-name, .studio-description') : [];
                for (var k = 0; k < names.length; k++) {
                    if (!names[k].dataset.wm) {
                        names[k].textContent = addWatermark(names[k].textContent);
                        names[k].dataset.wm = '1';
                    }
                }
            }
        }
    });
    observer.observe(document.body, { childList: true, subtree: true });

    // ===== LAYER 9: Obfuscate Data URLs =====
    // Make it harder to find the JSON data endpoints by checking referrer
    var origXHRSend = XMLHttpRequest.prototype.send;
    XMLHttpRequest.prototype.send = function () {
        // Add custom header that bots won't have
        try { this.setRequestHeader('X-Yoga-Client', 'web-' + Date.now()); } catch (e) {}
        return origXHRSend.apply(this, arguments);
    };

    // ===== LAYER 10: Console Warning =====
    console.log(
        '%c\u26A0 STOP!',
        'color:red;font-size:50px;font-weight:bold;text-shadow:1px 1px 2px black;'
    );
    console.log(
        '%cDie Daten auf dieser Website sind urheberrechtlich geschützt.\nAutomatisches Scraping, Kopieren oder Weiterverbreiten der Daten ist untersagt.\n\nThe data on this website is protected. Automated scraping, copying or redistribution is prohibited.',
        'color:#333;font-size:14px;'
    );

})();
