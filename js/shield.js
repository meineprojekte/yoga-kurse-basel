/* ============================================================
   YOGA SCHWEIZ — Shield v3 (non-invasive)
   Protects against scraping WITHOUT breaking site functionality
   ============================================================ */

(function () {
    'use strict';

    var ua = navigator.userAgent || '';

    // Allow search engines and social media through immediately
    if (/Googlebot|Bingbot|Google-InspectionTool|YandexBot|facebookexternalhit|Twitterbot|LinkedInBot|WhatsApp|Slackbot|TelegramBot|Discordbot|Applebot/i.test(ua)) {
        return;
    }

    // --- Bot score ---
    var score = 0;

    // 1. Known scraper user agents
    var scraperUA = [
        /python-requests/i, /python-urllib/i, /scrapy/i, /wget/i, /curl\//i,
        /java\//i, /perl/i, /ruby/i, /php\//i, /go-http/i, /node-fetch/i,
        /okhttp/i, /axios/i, /httpie/i, /postman/i, /insomnia/i,
        /selenium/i, /phantomjs/i, /puppeteer/i, /playwright/i, /headless/i,
        /httrack/i, /gptbot/i, /chatgpt/i, /ccbot/i, /anthropic/i, /bytespider/i,
        /semrush/i, /ahrefs/i, /mj12bot/i, /dotbot/i, /dataforseo/i,
        /megaindex/i, /blexbot/i, /sogou/i, /baidu/i, /colly/i, /goutte/i
    ];
    for (var i = 0; i < scraperUA.length; i++) {
        if (scraperUA[i].test(ua)) { score += 80; break; }
    }

    // 2. Headless browser detection
    if (navigator.webdriver) score += 50;
    if (!navigator.languages || navigator.languages.length === 0) score += 20;
    if (/Chrome/.test(ua) && !window.chrome) score += 30;

    // 3. Automation properties
    var autoProps = ['__webdriver_evaluate', '__selenium_evaluate', '__driver_evaluate', '_phantom', '__nightmare', '_selenium'];
    for (var a = 0; a < autoProps.length; a++) {
        if (window[autoProps[a]] !== undefined) { score += 40; break; }
    }

    // 4. Canvas test
    try {
        var c = document.createElement('canvas');
        c.width = 100; c.height = 30;
        var ctx = c.getContext('2d');
        ctx.fillStyle = '#f60';
        ctx.fillRect(0, 0, 100, 30);
        ctx.fillStyle = '#069';
        ctx.font = '12px Arial';
        ctx.fillText('test', 2, 15);
        if (c.toDataURL().length < 500) score += 20;
    } catch (e) { score += 10; }

    // 5. WebGL check
    try {
        var gl = document.createElement('canvas').getContext('webgl');
        if (gl) {
            var dbg = gl.getExtension('WEBGL_debug_renderer_info');
            if (dbg && /SwiftShader|llvmpipe|Mesa/i.test(gl.getParameter(dbg.UNMASKED_RENDERER_WEBGL))) {
                score += 30;
            }
        } else { score += 15; }
    } catch (e) {}

    // If bot detected, just log it (don't break the site)
    if (score >= 50) {
        console.log('%c\u26D4 Bot detected (score: ' + score + '). Activity logged.', 'color:red;font-size:14px;');
    }

    // --- Protections that DON'T break site functionality ---

    // Anti right-click (except on inputs)
    document.addEventListener('contextmenu', function (e) {
        if (e.target.tagName === 'INPUT' || e.target.tagName === 'TEXTAREA' || e.target.tagName === 'SELECT') return;
        e.preventDefault();
    });

    // Anti text selection on data cards (not on inputs/guide)
    document.addEventListener('selectstart', function (e) {
        var t = e.target.tagName;
        if (t === 'INPUT' || t === 'TEXTAREA' || t === 'SELECT') return;
        if (e.target.closest && (e.target.closest('.guide-content') || e.target.closest('.faq-answer') || e.target.closest('.feedback-form'))) return;
        e.preventDefault();
    });

    // Block Ctrl+U (view source), Ctrl+S (save), F12
    document.addEventListener('keydown', function (e) {
        if (e.target.tagName === 'INPUT' || e.target.tagName === 'TEXTAREA') return;
        if ((e.ctrlKey || e.metaKey) && (e.key === 'u' || e.key === 'U' || e.key === 's' || e.key === 'S')) e.preventDefault();
        if ((e.ctrlKey || e.metaKey) && e.shiftKey && (e.key === 'I' || e.key === 'i' || e.key === 'J' || e.key === 'j')) e.preventDefault();
        if (e.key === 'F12') e.preventDefault();
    });

    // Anti drag
    document.addEventListener('dragstart', function (e) { e.preventDefault(); });

    // Anti iframe
    if (window.top !== window.self) {
        try { window.top.location = window.self.location; } catch (e) {
            document.body.innerHTML = '<p style="padding:40px;text-align:center;">Cannot display in frame.</p>';
        }
    }

    // Clipboard: append source attribution
    document.addEventListener('copy', function (e) {
        if (e.target.tagName === 'INPUT' || e.target.tagName === 'TEXTAREA') return;
        var sel = window.getSelection();
        if (!sel || sel.toString().length < 20) return;
        e.preventDefault();
        if (e.clipboardData) {
            e.clipboardData.setData('text/plain', sel.toString() + '\n\n[Quelle: YogaSchweiz - Kopieren ohne Genehmigung untersagt]');
        }
    });

    // Watermark: invisible chars in studio data
    var wmObserver = new MutationObserver(function (muts) {
        for (var m = 0; m < muts.length; m++) {
            var nodes = muts[m].addedNodes;
            for (var n = 0; n < nodes.length; n++) {
                if (nodes[n].nodeType !== 1) continue;
                var els = nodes[n].querySelectorAll ? nodes[n].querySelectorAll('.studio-name, .studio-description') : [];
                for (var k = 0; k < els.length; k++) {
                    if (!els[k].dataset.wm) {
                        var txt = els[k].textContent;
                        var wm = '';
                        for (var c = 0; c < txt.length; c++) {
                            wm += txt[c];
                            if (c > 0 && c % 18 === 0) wm += '\u200B';
                        }
                        els[k].textContent = wm;
                        els[k].dataset.wm = '1';
                    }
                }
            }
        }
    });
    wmObserver.observe(document.body, { childList: true, subtree: true });

    // Honeypot links
    var traps = ['/api/v1/studios', '/data/export.json', '/admin/database'];
    for (var h = 0; h < traps.length; h++) {
        var hp = document.createElement('a');
        hp.href = traps[h];
        hp.textContent = 'data';
        hp.style.cssText = 'position:absolute;left:-9999px;top:-9999px;opacity:0;height:1px;width:1px;overflow:hidden;';
        hp.setAttribute('aria-hidden', 'true');
        hp.setAttribute('tabindex', '-1');
        document.body.appendChild(hp);
    }

    // Decoy data
    var decoyDiv = document.createElement('div');
    decoyDiv.style.cssText = 'position:absolute;left:-99999px;top:-99999px;width:1px;height:1px;overflow:hidden;opacity:0;';
    decoyDiv.setAttribute('aria-hidden', 'true');
    decoyDiv.innerHTML = '<div class="studio-card"><h3 class="studio-name">Phantom Yoga</h3><p>Fake Street 1, 0000 Nowhere</p></div>' +
        '<div class="studio-card"><h3 class="studio-name">Ghost Flow Center</h3><p>Trap Road 2, 0000 Decoy</p></div>';
    document.body.appendChild(decoyDiv);

    // Print protection via CSS
    var printCSS = document.createElement('style');
    printCSS.textContent = '@media print{.studio-card,.schedule-row,.guide-comparison-table{display:none!important}body::after{content:"Drucken nicht erlaubt - yogaschweiz online besuchen";display:block;padding:40px;text-align:center;font-size:20px}}';
    document.head.appendChild(printCSS);

    // Console warning
    console.log('%c\u26A0 STOP!', 'color:red;font-size:50px;font-weight:bold;');
    console.log('%cDiese Website ist geschützt. Scraping wird erkannt und blockiert.\nThis website is protected. Scraping is detected and blocked.', 'color:#333;font-size:13px;');

})();
