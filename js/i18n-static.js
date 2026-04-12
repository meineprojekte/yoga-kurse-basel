/**
 * i18n-static.js — Lightweight client-side translation for static pages
 * Reads ?lang= from URL and translates structural UI elements.
 * Supports: en, fr, it (de is the default, no translation needed).
 */
(function () {
    var params = new URLSearchParams(window.location.search);
    var lang = params.get('lang');
    if (!lang || ['en', 'fr', 'it'].indexOf(lang) === -1) return;

    // -- Update <html lang> --
    document.documentElement.lang = lang;

    // -- Canton name translations (DE → target) --
    var cn = {
        'Zürich':           { en: 'Zurich', fr: 'Zurich', it: 'Zurigo' },
        'Bern':             { en: 'Bern', fr: 'Berne', it: 'Berna' },
        'Luzern':           { en: 'Lucerne', fr: 'Lucerne', it: 'Lucerna' },
        'Uri':              { en: 'Uri', fr: 'Uri', it: 'Uri' },
        'Schwyz':           { en: 'Schwyz', fr: 'Schwyz', it: 'Svitto' },
        'Obwalden':         { en: 'Obwalden', fr: 'Obwald', it: 'Obvaldo' },
        'Nidwalden':        { en: 'Nidwalden', fr: 'Nidwald', it: 'Nidvaldo' },
        'Glarus':           { en: 'Glarus', fr: 'Glaris', it: 'Glarona' },
        'Zug':              { en: 'Zug', fr: 'Zoug', it: 'Zugo' },
        'Freiburg':         { en: 'Fribourg', fr: 'Fribourg', it: 'Friburgo' },
        'Solothurn':        { en: 'Solothurn', fr: 'Soleure', it: 'Soletta' },
        'Basel-Stadt':      { en: 'Basel-Stadt', fr: 'Bâle-Ville', it: 'Basilea Città' },
        'Basel-Landschaft': { en: 'Basel-Landschaft', fr: 'Bâle-Campagne', it: 'Basilea Campagna' },
        'Schaffhausen':     { en: 'Schaffhausen', fr: 'Schaffhouse', it: 'Sciaffusa' },
        'Appenzell A.Rh.':  { en: 'Appenzell A.Rh.', fr: 'Appenzell Rh.-Ext.', it: 'Appenzello Est.' },
        'Appenzell I.Rh.':  { en: 'Appenzell I.Rh.', fr: 'Appenzell Rh.-Int.', it: 'Appenzello Int.' },
        'St. Gallen':       { en: 'St. Gallen', fr: 'Saint-Gall', it: 'San Gallo' },
        'Graubünden':       { en: 'Graubünden', fr: 'Grisons', it: 'Grigioni' },
        'Aargau':           { en: 'Aargau', fr: 'Argovie', it: 'Argovia' },
        'Thurgau':          { en: 'Thurgau', fr: 'Thurgovie', it: 'Turgovia' },
        'Tessin':           { en: 'Ticino', fr: 'Tessin', it: 'Ticino' },
        'Waadt':            { en: 'Vaud', fr: 'Vaud', it: 'Vaud' },
        'Wallis':           { en: 'Valais', fr: 'Valais', it: 'Vallese' },
        'Neuenburg':        { en: 'Neuchâtel', fr: 'Neuchâtel', it: 'Neuchâtel' },
        'Genf':             { en: 'Geneva', fr: 'Genève', it: 'Ginevra' },
        'Jura':             { en: 'Jura', fr: 'Jura', it: 'Giura' }
    };

    // -- UI string translations --
    var ui = {
        en: {
            home: 'Home', studios: 'Studios', schedule: 'Schedule', cantons: 'Cantons', blog: 'Blog',
            toc: 'Table of Contents', readTime: 'min read', skip: 'Skip to content',
            languages: 'Languages', classesWeek: 'Classes/Week', yogaStyles: 'Yoga Styles',
            yogaIn: 'Yoga in', yogaInCanton: 'Yoga in Canton', yogaStudiosIn: 'Yoga Studios in',
            scheduleDash: 'Schedule —', related: 'Related Articles', otherCantons: 'Yoga in Other Cantons',
            cantonSub: 'Canton {n} ({c}) — All yoga studios and classes at a glance',
            titlePat: 'Yoga in {n} 2026 — {x} Studios, Classes & Schedule | Yoga Switzerland',
            footerMain: 'All yoga studios and classes in Switzerland',
            footerCopy: '\u00a9 2026 YogaSchweiz. All information without guarantee. Data is regularly updated.',
            footerTip: 'For current class times and prices, please visit the studio websites directly.',
            footerBlog: '\u00a9 2026 YogaSchweiz \u00b7 266 Studios in 26 Cantons \u00b7',
            faq: 'Frequently Asked Questions (FAQ)', allCantons: 'All Cantons',
            yogaStylesTitle: 'Yoga Styles', yogaBlog: 'Yoga Blog Switzerland',
            aboutTitle: 'About Yoga Kurse Switzerland', privacyTitle: 'Privacy Policy',
            mission: 'Our Mission', dataCollection: 'How We Collect and Verify Data',
            independence: 'Independence and Funding', langSection: 'Languages',
            technology: 'Technology', contact: 'Contact',
            discover: 'Discover all 266 studios \u2192',
            authorBio: 'Independent information portal for yoga in Switzerland. We research, compare and recommend \u2014 neutral and without paid placements.',
            siteName: 'Yoga Switzerland', allCantonsNav: 'All Cantons'
        },
        fr: {
            home: 'Accueil', studios: 'Studios', schedule: 'Horaire', cantons: 'Cantons', blog: 'Blog',
            toc: 'Sommaire', readTime: 'min de lecture', skip: 'Aller au contenu',
            languages: 'Langues', classesWeek: 'Cours/Semaine', yogaStyles: 'Styles de yoga',
            yogaIn: 'Yoga \u00e0', yogaInCanton: 'Yoga dans le canton de', yogaStudiosIn: 'Studios de yoga \u00e0',
            scheduleDash: 'Horaire \u2014', related: 'Articles connexes', otherCantons: 'Yoga dans d\u2019autres cantons',
            cantonSub: 'Canton de {n} ({c}) \u2014 Tous les studios et cours de yoga en un coup d\u2019\u0153il',
            titlePat: 'Yoga \u00e0 {n} 2026 \u2014 {x} Studios, Cours & Horaire | Yoga Suisse',
            footerMain: 'Tous les studios de yoga et cours en Suisse',
            footerCopy: '\u00a9 2026 YogaSchweiz. Toutes les informations sans garantie. Donn\u00e9es mises \u00e0 jour r\u00e9guli\u00e8rement.',
            footerTip: 'Pour les horaires et prix actuels, veuillez consulter les sites web des studios.',
            footerBlog: '\u00a9 2026 YogaSchweiz \u00b7 266 Studios dans 26 cantons \u00b7',
            faq: 'Questions fr\u00e9quentes (FAQ)', allCantons: 'Tous les cantons',
            yogaStylesTitle: 'Styles de yoga', yogaBlog: 'Blog Yoga Suisse',
            aboutTitle: '\u00c0 propos de Yoga Cours Suisse', privacyTitle: 'Politique de confidentialit\u00e9',
            mission: 'Notre mission', dataCollection: 'Comment nous collectons et v\u00e9rifions les donn\u00e9es',
            independence: 'Ind\u00e9pendance et financement', langSection: 'Langues',
            technology: 'Technologie', contact: 'Contact',
            discover: 'D\u00e9couvrir les 266 studios \u2192',
            authorBio: 'Portail d\u2019information ind\u00e9pendant pour le yoga en Suisse. Nous recherchons, comparons et recommandons \u2014 neutre et sans placement payant.',
            siteName: 'Yoga Suisse', allCantonsNav: 'Tous les cantons'
        },
        it: {
            home: 'Home', studios: 'Studi', schedule: 'Orario', cantons: 'Cantoni', blog: 'Blog',
            toc: 'Indice', readTime: 'min di lettura', skip: 'Vai al contenuto',
            languages: 'Lingue', classesWeek: 'Corsi/Settimana', yogaStyles: 'Stili di yoga',
            yogaIn: 'Yoga a', yogaInCanton: 'Yoga nel Cantone di', yogaStudiosIn: 'Studi di yoga a',
            scheduleDash: 'Orario \u2014', related: 'Articoli correlati', otherCantons: 'Yoga in altri cantoni',
            cantonSub: 'Cantone di {n} ({c}) \u2014 Tutti gli studi e i corsi di yoga a colpo d\u2019occhio',
            titlePat: 'Yoga a {n} 2026 \u2014 {x} Studi, Corsi & Orario | Yoga Svizzera',
            footerMain: 'Tutti gli studi e i corsi di yoga in Svizzera',
            footerCopy: '\u00a9 2026 YogaSchweiz. Tutte le informazioni senza garanzia. Dati aggiornati regolarmente.',
            footerTip: 'Per orari e prezzi attuali, visitare direttamente i siti web degli studi.',
            footerBlog: '\u00a9 2026 YogaSchweiz \u00b7 266 Studi in 26 Cantoni \u00b7',
            faq: 'Domande frequenti (FAQ)', allCantons: 'Tutti i cantoni',
            yogaStylesTitle: 'Stili di yoga', yogaBlog: 'Blog Yoga Svizzera',
            aboutTitle: 'Informazioni su Yoga Corsi Svizzera', privacyTitle: 'Informativa sulla privacy',
            mission: 'La nostra missione', dataCollection: 'Come raccogliamo e verifichiamo i dati',
            independence: 'Indipendenza e finanziamento', langSection: 'Lingue',
            technology: 'Tecnologia', contact: 'Contatto',
            discover: 'Scopri tutti i 266 studi \u2192',
            authorBio: 'Portale informativo indipendente per lo yoga in Svizzera. Ricerchiamo, confrontiamo e raccomandiamo \u2014 in modo neutrale e senza posizionamenti a pagamento.',
            siteName: 'Yoga Svizzera', allCantonsNav: 'Tutti i cantoni'
        }
    };

    var t = ui[lang];
    if (!t) return;

    function tc(name) { return (cn[name] && cn[name][lang]) || name; }

    var path = window.location.pathname;
    var isCanton = /\/kanton\/[^/]+\//.test(path);
    var isCantonIdx = /\/kanton\/?$/.test(path);
    var isBlogPost = /\/blog\/[^/]+\//.test(path) && !/\/blog\/?$/.test(path);
    var isBlogIdx = /\/blog\/?$/.test(path);
    var isYoga = /\/yoga\/?$/.test(path);
    var isAbout = /\/about\/?$/.test(path);
    var isPrivacy = /\/datenschutz\/?$/.test(path);

    // === CANTON INDIVIDUAL PAGES ===
    if (isCanton) {
        // Nav
        document.querySelectorAll('.canton-nav a').forEach(function (a) {
            var x = a.textContent.trim();
            if (x === 'Home') a.textContent = t.home;
            else if (x === 'Studios') a.textContent = t.studios;
            else if (x === 'Stundenplan') a.textContent = t.schedule;
            else if (x === 'Kantone') a.textContent = t.cantons;
        });
        // Breadcrumb
        var bc = document.querySelector('.canton-breadcrumb');
        if (bc) {
            bc.childNodes.forEach(function (n) {
                if (n.nodeType === 3) n.textContent = n.textContent.replace('Kantone', t.cantons);
                if (n.tagName === 'A' && n.textContent.trim() === 'Home') n.textContent = t.home;
            });
        }
        // Stats
        document.querySelectorAll('.stat-label').forEach(function (el) {
            var x = el.textContent.trim();
            if (x === 'Studios') el.textContent = t.studios;
            else if (x === 'Kurse/Woche') el.textContent = t.classesWeek;
            else if (x === 'Yoga-Stile') el.textContent = t.yogaStyles;
        });
        // Hero subtitle
        var sub = document.querySelector('.canton-subtitle');
        if (sub) {
            var m = sub.textContent.match(/Kanton\s+(.+?)\s+\((\w+)\)/);
            if (m) sub.textContent = t.cantonSub.replace('{n}', tc(m[1])).replace('{c}', m[2]);
        }
        // Headings
        document.querySelectorAll('h1, h2').forEach(function (h) {
            var x = h.textContent.trim(), m;
            if ((m = x.match(/^Yoga in (.+)$/)))
                h.textContent = t.yogaIn + ' ' + tc(m[1]);
            else if ((m = x.match(/^Yoga im Kanton (.+)$/)))
                h.textContent = t.yogaInCanton + ' ' + tc(m[1]);
            else if ((m = x.match(/^Yoga-Studios in (.+?) \((\d+)\)$/)))
                h.textContent = t.yogaStudiosIn + ' ' + tc(m[1]) + ' (' + m[2] + ')';
            else if ((m = x.match(/^Stundenplan — (.+)$/)))
                h.textContent = t.scheduleDash + ' ' + tc(m[1]);
            else if (x === 'Weiterführende Artikel')
                h.textContent = t.related;
            else if (x === 'Yoga in anderen Kantonen')
                h.textContent = t.otherCantons;
        });
        // Studio labels
        document.querySelectorAll('.studio-languages').forEach(function (el) {
            el.textContent = el.textContent.replace('Sprachen:', t.languages + ':');
        });
        // Canton links
        document.querySelectorAll('.canton-link').forEach(function (a) {
            var m = a.textContent.match(/^(.+?) \((\w+\.?)\)$/);
            if (m) a.textContent = tc(m[1]) + ' (' + m[2] + ')';
        });
        // Title
        var tm = document.title.match(/Yoga in (.+?) 2026 — (\d+) Studios/);
        if (tm) document.title = t.titlePat.replace('{n}', tc(tm[1])).replace('{x}', tm[2]);
        // Footer
        var ft = document.querySelector('.canton-footer');
        if (ft) {
            var ps = ft.querySelectorAll('p');
            if (ps[0]) {
                var a = ps[0].querySelector('a');
                if (a) a.textContent = t.siteName;
                ps[0].childNodes.forEach(function (n) {
                    if (n.nodeType === 3 && n.textContent.indexOf('Alle Yoga') > -1)
                        n.textContent = ' \u2014 ' + t.footerMain;
                });
            }
            if (ps[1]) ps[1].textContent = t.footerCopy;
            if (ps[2]) ps[2].textContent = t.footerTip;
        }
    }

    // === CANTON INDEX ===
    if (isCantonIdx) {
        document.querySelectorAll('h1').forEach(function (h) {
            if (h.textContent.trim() === 'Alle Kantone') h.textContent = t.allCantons;
        });
        document.title = t.allCantons + ' \u2014 ' + t.siteName;
        // Translate canton card names
        document.querySelectorAll('.canton-link, .canton-card-title, a[href*="/kanton/"]').forEach(function (el) {
            var m = el.textContent.match(/^(.+?) \((\w+\.?)\)$/);
            if (m) el.textContent = tc(m[1]) + ' (' + m[2] + ')';
        });
    }

    // === BLOG POST PAGES ===
    if (isBlogPost) {
        // Nav
        document.querySelectorAll('.nav-links a').forEach(function (a) {
            var x = a.textContent.trim();
            if (x === 'Studios') a.textContent = t.studios;
            else if (x === 'Blog') a.textContent = t.blog;
        });
        // Skip link
        var skip = document.querySelector('.skip-link');
        if (skip) skip.textContent = t.skip;
        // Breadcrumb
        document.querySelectorAll('.breadcrumb a').forEach(function (a) {
            if (a.textContent.trim() === 'Home') a.textContent = t.home;
        });
        // Reading time
        var meta = document.querySelector('.meta');
        if (meta) meta.textContent = meta.textContent.replace('Min. Lesezeit', t.readTime);
        // TOC
        document.querySelectorAll('.toc h2').forEach(function (h) {
            if (h.textContent.trim() === 'Inhaltsverzeichnis') h.textContent = t.toc;
        });
        // FAQ heading
        document.querySelectorAll('h2').forEach(function (h) {
            if (/Häufig gestellte Fragen/.test(h.textContent)) h.textContent = t.faq;
        });
        // Author box
        var ai = document.querySelector('.author-info p');
        if (ai) {
            var al = ai.querySelector('a');
            if (al) al.textContent = t.discover;
            ai.childNodes.forEach(function (n) {
                if (n.nodeType === 3 && /Unabhängig/.test(n.textContent)) n.textContent = t.authorBio + ' ';
            });
        }
        // Footer
        var bf = document.querySelector('.footer p');
        if (bf) bf.innerHTML = t.footerBlog + ' <a href="/">YogaSchweiz</a> \u00b7 <a href="/blog/">' + t.blog + '</a>';
    }

    // === BLOG INDEX ===
    if (isBlogIdx) {
        document.querySelectorAll('.nav-links a').forEach(function (a) {
            var x = a.textContent.trim();
            if (x === 'Studios') a.textContent = t.studios;
            else if (x === 'Blog') a.textContent = t.blog;
        });
        document.querySelectorAll('h1').forEach(function (h) {
            if (/Yoga Blog/.test(h.textContent)) h.textContent = t.yogaBlog;
        });
        document.title = t.yogaBlog;
        document.querySelectorAll('.breadcrumb a').forEach(function (a) {
            if (a.textContent.trim() === 'Home') a.textContent = t.home;
        });
    }

    // === YOGA STYLES PAGE ===
    if (isYoga) {
        document.querySelectorAll('h1').forEach(function (h) {
            if (h.textContent.trim() === 'Yoga-Stile') h.textContent = t.yogaStylesTitle;
        });
        document.title = t.yogaStylesTitle + ' \u2014 ' + t.siteName;
    }

    // === ABOUT PAGE ===
    if (isAbout) {
        document.querySelectorAll('.nav-links a').forEach(function (a) {
            var x = a.textContent.trim();
            if (x === 'Studios') a.textContent = t.studios;
            else if (x === 'Blog') a.textContent = t.blog;
        });
        document.querySelectorAll('h1').forEach(function (h) {
            if (/Über/.test(h.textContent)) h.textContent = t.aboutTitle;
        });
        document.title = t.aboutTitle + ' \u2014 ' + t.siteName;
        var headingMap = {
            'Unsere Mission': t.mission,
            'Wie wir Daten sammeln und verifizieren': t.dataCollection,
            'Unabhängigkeit und Finanzierung': t.independence,
            'Sprachen': t.langSection,
            'Technologie': t.technology,
            'Kontakt': t.contact
        };
        document.querySelectorAll('h2').forEach(function (h) {
            var x = h.textContent.trim();
            if (headingMap[x]) h.textContent = headingMap[x];
        });
        document.querySelectorAll('.breadcrumb a').forEach(function (a) {
            if (a.textContent.trim() === 'Home') a.textContent = t.home;
        });
    }

    // === PRIVACY PAGE ===
    if (isPrivacy) {
        document.querySelectorAll('.nav-links a').forEach(function (a) {
            var x = a.textContent.trim();
            if (x === 'Studios') a.textContent = t.studios;
            else if (x === 'Blog') a.textContent = t.blog;
        });
        document.querySelectorAll('h1').forEach(function (h) {
            if (/Datenschutz/.test(h.textContent)) h.textContent = t.privacyTitle;
        });
        document.title = t.privacyTitle + ' \u2014 ' + t.siteName;
        document.querySelectorAll('.breadcrumb a').forEach(function (a) {
            if (a.textContent.trim() === 'Home') a.textContent = t.home;
        });
    }

    // === SHARED: Nav for pages using mainNav (kanton index, yoga styles) ===
    if (isCantonIdx || isYoga) {
        document.querySelectorAll('#mainNav a').forEach(function (a) {
            var x = a.textContent.trim();
            if (x === 'Home') a.textContent = t.home;
            else if (x === 'Studios') a.textContent = t.studios;
            else if (x === 'Kantone' || x === 'Alle Kantone') a.textContent = t.allCantonsNav;
            else if (x === 'Yoga-Stile') a.textContent = t.yogaStylesTitle;
            else if (x === 'Blog') a.textContent = t.blog;
        });
    }

    // === SHARED: Footer for blog-style pages ===
    if (isBlogIdx || isAbout || isPrivacy) {
        var fp = document.querySelector('.footer p');
        if (fp) fp.innerHTML = t.footerBlog + ' <a href="/">YogaSchweiz</a> \u00b7 <a href="/blog/">' + t.blog + '</a>';
    }

    // === SHARED: Footer for kanton index & yoga styles ===
    if (isCantonIdx || isYoga) {
        var fq = document.querySelector('.footer');
        if (fq) {
            var ps = fq.querySelectorAll('p');
            if (ps.length) {
                ps[0].innerHTML = '<a href="/">' + t.siteName + '</a> \u2014 ' + t.footerMain;
                if (ps[1]) ps[1].textContent = t.footerCopy;
            }
        }
    }

    // === SHARED: Update OG locale ===
    var og = document.querySelector('meta[property="og:locale"]');
    if (og) og.content = { en: 'en_GB', fr: 'fr_CH', it: 'it_CH' }[lang] || og.content;

    // === SHARED: Update meta description start pattern ===
    var md = document.querySelector('meta[name="description"]');
    if (md && isCanton) {
        md.content = md.content.replace(/^Yoga im Kanton/, t.yogaInCanton);
    }
})();
