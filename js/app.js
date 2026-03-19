/* ============================================================
   YOGA KURSE BASEL — Main Application
   ============================================================ */

(function () {
    'use strict';

    // --- i18n translations ---
    var translations = {
        de: {
            'nav.studios': 'Studios',
            'nav.styles': 'Yoga-Stile',
            'nav.map': 'Karte',
            'nav.faq': 'FAQ',
            'hero.title': 'Alle Yoga-Kurse in Basel<br><span class="hero-accent">auf einen Blick</span>',
            'hero.subtitle': '40+ Studios &bull; 30+ Yoga-Stile &bull; Täglich aktualisiert',
            'hero.search_placeholder': 'Studio, Yoga-Stil oder Quartier suchen...',
            'hero.stat_studios': 'Studios',
            'hero.stat_styles': 'Yoga-Stile',
            'hero.stat_updates': 'täglich aktualisiert',
            'filters.title': 'Filter',
            'filters.button': 'Filter & Sortierung',
            'filters.all': 'Alle',
            'filters.style': 'Yoga-Stil',
            'filters.all_styles': 'Alle Stile',
            'filters.district': 'Quartier / Gebiet',
            'filters.all_districts': 'Alle Quartiere',
            'filters.surrounding': 'Umgebung',
            'filters.feature': 'Besonderheiten',
            'filters.all_features': 'Alle',
            'filters.sort': 'Sortierung',
            'filters.sort_name': 'Name (A-Z)',
            'filters.sort_styles': 'Anzahl Stile',
            'filters.sort_district': 'Quartier',
            'filters.reset': 'Filter zurücksetzen',
            'filters.clear_all': 'Alle Filter löschen',
            'results.showing': 'Zeige',
            'results.of': 'von',
            'results.studios': 'Studios',
            'results.export_pdf': 'PDF herunterladen',
            'results.none_title': 'Keine Studios gefunden',
            'results.none_text': 'Versuche andere Filter oder Suchbegriffe.',
            'studios.title': 'Yoga-Studios in Basel',
            'styles.title': 'Yoga-Stile in Basel',
            'styles.subtitle': 'Entdecke die Vielfalt der Yoga-Stile, die in Basel angeboten werden',
            'map.title': 'Studios auf der Karte',
            'map.subtitle': 'Finde Yoga-Studios in deiner Nähe',
            'faq.title': 'Häufige Fragen',
            'footer.desc': 'Die vollständige, unabhängige Übersicht aller Yoga-Kurse und Studios in Basel und Umgebung.',
            'footer.quick_links': 'Schnellzugriff',
            'footer.popular_styles': 'Beliebte Stile',
            'footer.booking': 'Buchungsplattformen',
            'footer.disclaimer': 'Diese Website ist ein unabhängiges Informationsportal und steht in keiner geschäftlichen Verbindung zu den aufgeführten Studios. Alle Informationen stammen aus öffentlich zugänglichen Quellen. Für aktuelle Preise und Stundenpläne besuche bitte die jeweilige Studio-Website.',
            'footer.updated': 'Letzte Aktualisierung:',
            'modal.website': 'Zur Website',
            'modal.schedule': 'Stundenplan ansehen',
            'modal.styles': 'Yoga-Stile',
            'modal.teachers': 'Lehrer/innen',
            'modal.features': 'Besonderheiten',
            'modal.contact': 'Kontakt',
            'modal.hours': 'Öffnungszeiten',
            'modal.languages': 'Sprachen',
            'modal.booking': 'Buchung über',
            'card.teachers': 'Lehrer/innen',
            'card.more_styles': 'weitere',
            'card.details': 'Details',
            'styles.studios_count': 'Studios',
            'pdf.title': 'Yoga-Studios in Basel — Übersicht',
            'pdf.generated': 'Erstellt am'
        },
        en: {
            'nav.studios': 'Studios',
            'nav.styles': 'Yoga Styles',
            'nav.map': 'Map',
            'nav.faq': 'FAQ',
            'hero.title': 'All Yoga Classes in Basel<br><span class="hero-accent">at a Glance</span>',
            'hero.subtitle': '40+ Studios &bull; 30+ Yoga Styles &bull; Updated Daily',
            'hero.search_placeholder': 'Search studio, yoga style or district...',
            'hero.stat_studios': 'Studios',
            'hero.stat_styles': 'Yoga Styles',
            'hero.stat_updates': 'daily updates',
            'filters.title': 'Filters',
            'filters.button': 'Filters & Sorting',
            'filters.all': 'All',
            'filters.style': 'Yoga Style',
            'filters.all_styles': 'All Styles',
            'filters.district': 'District / Area',
            'filters.all_districts': 'All Districts',
            'filters.surrounding': 'Surrounding Area',
            'filters.feature': 'Features',
            'filters.all_features': 'All',
            'filters.sort': 'Sort By',
            'filters.sort_name': 'Name (A-Z)',
            'filters.sort_styles': 'Number of Styles',
            'filters.sort_district': 'District',
            'filters.reset': 'Reset Filters',
            'filters.clear_all': 'Clear All Filters',
            'results.showing': 'Showing',
            'results.of': 'of',
            'results.studios': 'Studios',
            'results.export_pdf': 'Download PDF',
            'results.none_title': 'No studios found',
            'results.none_text': 'Try different filters or search terms.',
            'studios.title': 'Yoga Studios in Basel',
            'styles.title': 'Yoga Styles in Basel',
            'styles.subtitle': 'Discover the variety of yoga styles offered in Basel',
            'map.title': 'Studios on the Map',
            'map.subtitle': 'Find yoga studios near you',
            'faq.title': 'Frequently Asked Questions',
            'footer.desc': 'The complete, independent overview of all yoga classes and studios in Basel and surroundings.',
            'footer.quick_links': 'Quick Links',
            'footer.popular_styles': 'Popular Styles',
            'footer.booking': 'Booking Platforms',
            'footer.disclaimer': 'This website is an independent information portal and has no business affiliation with the listed studios. All information is sourced from publicly available data. For current prices and schedules, please visit the respective studio website.',
            'footer.updated': 'Last updated:',
            'modal.website': 'Visit Website',
            'modal.schedule': 'View Schedule',
            'modal.styles': 'Yoga Styles',
            'modal.teachers': 'Teachers',
            'modal.features': 'Special Features',
            'modal.contact': 'Contact',
            'modal.hours': 'Hours',
            'modal.languages': 'Languages',
            'modal.booking': 'Book via',
            'card.teachers': 'Teachers',
            'card.more_styles': 'more',
            'card.details': 'Details',
            'styles.studios_count': 'Studios',
            'pdf.title': 'Yoga Studios in Basel — Overview',
            'pdf.generated': 'Generated on'
        }
    };

    // --- State ---
    var state = {
        studios: [],
        filteredStudios: [],
        lang: 'de',
        theme: 'light',
        view: 'grid',
        activeStyleFilter: 'all',
        searchQuery: '',
        map: null,
        markers: []
    };

    // Read saved preferences
    try {
        state.lang = localStorage.getItem('yogabasel-lang') || 'de';
        state.theme = localStorage.getItem('yogabasel-theme') || 'light';
    } catch (e) {
        // localStorage not available
    }

    // --- Utility ---
    function escapeHtml(str) {
        if (!str) return '';
        var div = document.createElement('div');
        div.textContent = str;
        return div.innerHTML;
    }

    function $(id) {
        return document.getElementById(id);
    }

    function t(key) {
        return (translations[state.lang] || translations.de)[key] || key;
    }

    // --- Init: runs when DOM is ready ---
    function init() {
        console.log('[YogaBasel] Initializing...');
        applyTheme();
        applyLanguage();
        setupEventListeners();
        loadData();
        updateLastUpdated();
        console.log('[YogaBasel] Init complete.');
    }

    // Robust DOM ready detection
    if (document.readyState === 'loading') {
        document.addEventListener('DOMContentLoaded', init);
    } else {
        // DOM already parsed (script loaded with defer or after DOMContentLoaded)
        init();
    }

    // --- Data Loading ---
    function loadData() {
        // Determine base URL for data file
        var scriptEls = document.querySelectorAll('script[src*="app.js"]');
        var basePath = './';
        if (scriptEls.length > 0) {
            var src = scriptEls[0].getAttribute('src');
            basePath = src.replace('js/app.js', '').replace('app.js', '') || './';
        }

        var dataUrl = basePath + 'data/studios.json';
        console.log('[YogaBasel] Fetching data from:', dataUrl);

        var xhr = new XMLHttpRequest();
        xhr.open('GET', dataUrl, true);
        xhr.onreadystatechange = function () {
            if (xhr.readyState !== 4) return;
            if (xhr.status === 200) {
                try {
                    var data = JSON.parse(xhr.responseText);
                    state.studios = [];
                    for (var i = 0; i < data.studios.length; i++) {
                        if (data.studios[i].active) {
                            state.studios.push(data.studios[i]);
                        }
                    }
                    state.filteredStudios = state.studios.slice();
                    populateStyleFilter(data.styles_index || []);
                    $('studioCount').textContent = state.studios.length + '+';
                    $('totalCount').textContent = state.studios.length;
                    console.log('[YogaBasel] Loaded', state.studios.length, 'studios');
                    renderStudios();
                    renderStylesOverview();
                    initMap();
                } catch (e) {
                    console.error('[YogaBasel] Error parsing JSON:', e);
                    showError('Fehler beim Laden der Daten.');
                }
            } else {
                console.error('[YogaBasel] HTTP error:', xhr.status, 'URL:', dataUrl);
                showError('Daten konnten nicht geladen werden (HTTP ' + xhr.status + ').');
            }
        };
        xhr.onerror = function () {
            console.error('[YogaBasel] Network error loading data');
            showError('Netzwerkfehler beim Laden der Daten.');
        };
        xhr.send();
    }

    function showError(msg) {
        var grid = $('studiosGrid');
        if (grid) {
            grid.innerHTML = '<p style="grid-column:1/-1;text-align:center;padding:40px;color:#c00;font-weight:600;">' + escapeHtml(msg) + '</p>';
        }
    }

    function populateStyleFilter(styles) {
        var select = $('filterStyle');
        if (!select) return;
        for (var i = 0; i < styles.length; i++) {
            var opt = document.createElement('option');
            opt.value = styles[i];
            opt.textContent = styles[i];
            select.appendChild(opt);
        }
    }

    // --- Rendering ---
    function renderStudios() {
        var grid = $('studiosGrid');
        var noResults = $('noResults');
        var visibleCount = $('visibleCount');
        if (!grid) return;

        grid.innerHTML = '';

        if (state.filteredStudios.length === 0) {
            if (noResults) noResults.hidden = false;
            if (visibleCount) visibleCount.textContent = '0';
            return;
        }

        if (noResults) noResults.hidden = true;
        if (visibleCount) visibleCount.textContent = state.filteredStudios.length;

        for (var i = 0; i < state.filteredStudios.length; i++) {
            grid.appendChild(createStudioCard(state.filteredStudios[i], i));
        }
    }

    function createStudioCard(studio, index) {
        var card = document.createElement('article');
        card.className = 'studio-card';
        card.setAttribute('data-studio-id', studio.id);
        card.style.animationDelay = Math.min(index * 0.03, 0.3) + 's';

        var address = studio.addresses[0] || {};
        var addressText = address.street
            ? address.street + ', ' + (address.zip || '') + ' ' + (address.city || '') + (address.label ? ' — ' + address.label : '')
            : '';

        var maxTags = 4;
        var visibleStyles = studio.styles.slice(0, maxTags);
        var hiddenCount = Math.max(0, studio.styles.length - maxTags);
        var teacherNames = studio.teachers.slice(0, 3).join(', ');

        var stylesHtml = '';
        for (var j = 0; j < visibleStyles.length; j++) {
            stylesHtml += '<span class="style-tag">' + escapeHtml(visibleStyles[j]) + '</span>';
        }
        if (hiddenCount > 0) {
            stylesHtml += '<span class="style-tag more">+' + hiddenCount + ' ' + t('card.more_styles') + '</span>';
        }

        card.innerHTML =
            '<div class="studio-card-header">' +
                '<h3 class="studio-name">' + escapeHtml(studio.name) + '</h3>' +
                (studio.drop_in ? '<span class="studio-badge drop-in">Drop-in</span>' : '') +
            '</div>' +
            '<div class="studio-address">' +
                '<svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M21 10c0 7-9 13-9 13s-9-6-9-13a9 9 0 0 1 18 0z"/><circle cx="12" cy="10" r="3"/></svg>' +
                '<span>' + escapeHtml(addressText) + '</span>' +
            '</div>' +
            '<p class="studio-description">' + escapeHtml(studio.description) + '</p>' +
            '<div class="studio-styles">' + stylesHtml + '</div>' +
            '<div class="studio-footer">' +
                '<span class="studio-teachers">' +
                    (teacherNames ? '<svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M20 21v-2a4 4 0 0 0-4-4H8a4 4 0 0 0-4 4v2"/><circle cx="12" cy="7" r="4"/></svg> ' + escapeHtml(teacherNames) + (studio.teachers.length > 3 ? '...' : '') : '') +
                '</span>' +
                '<span class="studio-link">' + t('card.details') + ' &rarr;</span>' +
            '</div>';

        card.addEventListener('click', (function (s) {
            return function () { openModal(s); };
        })(studio));

        return card;
    }

    function renderStylesOverview() {
        var grid = $('stylesGrid');
        if (!grid) return;
        var styleCounts = {};

        for (var i = 0; i < state.studios.length; i++) {
            var styles = state.studios[i].styles;
            for (var j = 0; j < styles.length; j++) {
                styleCounts[styles[j]] = (styleCounts[styles[j]] || 0) + 1;
            }
        }

        var entries = [];
        for (var key in styleCounts) {
            if (styleCounts.hasOwnProperty(key)) {
                entries.push([key, styleCounts[key]]);
            }
        }
        entries.sort(function (a, b) { return b[1] - a[1]; });

        var html = '';
        for (var k = 0; k < entries.length; k++) {
            html += '<div class="style-card" data-style="' + escapeHtml(entries[k][0]) + '">' +
                '<div class="style-card-name">' + escapeHtml(entries[k][0]) + '</div>' +
                '<div class="style-card-count">' + entries[k][1] + ' ' + t('styles.studios_count') + '</div>' +
            '</div>';
        }
        grid.innerHTML = html;

        // Click handlers
        var cards = grid.querySelectorAll('.style-card');
        for (var m = 0; m < cards.length; m++) {
            cards[m].addEventListener('click', (function (card) {
                return function () {
                    filterByStyle(card.getAttribute('data-style'));
                    var studios = $('studios');
                    if (studios) studios.scrollIntoView({ behavior: 'smooth' });
                };
            })(cards[m]));
        }
    }

    // --- Modal ---
    function openModal(studio) {
        var overlay = $('modalOverlay');
        var content = $('modalContent');
        if (!overlay || !content) return;

        var addresses = '';
        for (var i = 0; i < studio.addresses.length; i++) {
            var a = studio.addresses[i];
            if (i > 0) addresses += '<br>';
            addresses += escapeHtml(a.street + ', ' + (a.zip || '') + ' ' + (a.city || '')) +
                (a.label ? ' (' + escapeHtml(a.label) + ')' : '');
        }

        var stylesHtml = '';
        for (var j = 0; j < studio.styles.length; j++) {
            stylesHtml += '<span class="style-tag">' + escapeHtml(studio.styles[j]) + '</span>';
        }

        var featuresHtml = '';
        var features = studio.special_features || [];
        for (var k = 0; k < features.length; k++) {
            featuresHtml += '<span class="feature-badge">' + escapeHtml(features[k]) + '</span>';
        }

        var html = '<h2 id="modalTitle">' + escapeHtml(studio.name) + '</h2>' +
            '<div class="modal-section">' +
                '<div class="modal-info-row">' +
                    '<svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M21 10c0 7-9 13-9 13s-9-6-9-13a9 9 0 0 1 18 0z"/><circle cx="12" cy="10" r="3"/></svg>' +
                    '<span>' + addresses + '</span>' +
                '</div>';

        if (studio.phone) {
            html += '<div class="modal-info-row"><svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M22 16.92v3a2 2 0 0 1-2.18 2 19.79 19.79 0 0 1-8.63-3.07 19.5 19.5 0 0 1-6-6 19.79 19.79 0 0 1-3.07-8.67A2 2 0 0 1 4.11 2h3a2 2 0 0 1 2 1.72c.127.96.361 1.903.7 2.81a2 2 0 0 1-.45 2.11L8.09 9.91a16 16 0 0 0 6 6l1.27-1.27a2 2 0 0 1 2.11-.45c.907.339 1.85.573 2.81.7A2 2 0 0 1 22 16.92z"/></svg><a href="tel:' + escapeHtml(studio.phone) + '">' + escapeHtml(studio.phone) + '</a></div>';
        }
        if (studio.email) {
            html += '<div class="modal-info-row"><svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M4 4h16c1.1 0 2 .9 2 2v12c0 1.1-.9 2-2 2H4c-1.1 0-2-.9-2-2V6c0-1.1.9-2 2-2z"/><polyline points="22,6 12,13 2,6"/></svg><a href="mailto:' + escapeHtml(studio.email) + '">' + escapeHtml(studio.email) + '</a></div>';
        }
        if (studio.hours) {
            html += '<div class="modal-info-row"><svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><circle cx="12" cy="12" r="10"/><polyline points="12 6 12 12 16 14"/></svg><span>' + escapeHtml(studio.hours) + '</span></div>';
        }
        if (studio.booking_platform) {
            html += '<div class="modal-info-row"><svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><rect x="3" y="4" width="18" height="18" rx="2" ry="2"/><line x1="16" y1="2" x2="16" y2="6"/><line x1="8" y1="2" x2="8" y2="6"/><line x1="3" y1="10" x2="21" y2="10"/></svg><span>' + t('modal.booking') + ': ' + escapeHtml(studio.booking_platform) + '</span></div>';
        }
        if (studio.languages && studio.languages.length > 0) {
            html += '<div class="modal-info-row"><svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><circle cx="12" cy="12" r="10"/><line x1="2" y1="12" x2="22" y2="12"/><path d="M12 2a15.3 15.3 0 0 1 4 10 15.3 15.3 0 0 1-4 10 15.3 15.3 0 0 1-4-10 15.3 15.3 0 0 1 4-10z"/></svg><span>' + t('modal.languages') + ': ' + studio.languages.join(', ') + '</span></div>';
        }

        html += '</div>' +
            '<p style="margin-bottom:24px;color:#666;font-size:14px;line-height:1.6;">' + escapeHtml(studio.description) + '</p>' +
            '<div class="modal-section"><h3>' + t('modal.styles') + '</h3><div class="modal-styles">' + stylesHtml + '</div></div>';

        if (studio.teachers.length > 0) {
            html += '<div class="modal-section"><h3>' + t('modal.teachers') + '</h3><p style="color:#666;font-size:14px;">' + escapeHtml(studio.teachers.join(', ')) + '</p></div>';
        }

        if (features.length > 0) {
            html += '<div class="modal-section"><h3>' + t('modal.features') + '</h3><div class="modal-features">' + featuresHtml + '</div></div>';
        }

        html += '<div class="modal-actions">';
        if (studio.website) {
            html += '<a href="' + escapeHtml(studio.website) + '" target="_blank" rel="noopener noreferrer" class="btn btn-primary">' + t('modal.website') + '</a>';
        }
        if (studio.schedule_url) {
            html += '<a href="' + escapeHtml(studio.schedule_url) + '" target="_blank" rel="noopener noreferrer" class="btn btn-outline">' + t('modal.schedule') + '</a>';
        }
        html += '</div>';

        content.innerHTML = html;
        overlay.classList.add('active');
        document.body.style.overflow = 'hidden';
    }

    function closeModal() {
        var overlay = $('modalOverlay');
        if (overlay) overlay.classList.remove('active');
        document.body.style.overflow = '';
    }

    // --- Filtering ---
    function applyFilters() {
        var results = state.studios.slice();
        var searchQ = state.searchQuery.toLowerCase().trim();

        // Search
        if (searchQ) {
            results = results.filter(function (s) {
                var parts = [s.name, s.description];
                parts = parts.concat(s.styles);
                parts = parts.concat(s.teachers);
                for (var i = 0; i < s.addresses.length; i++) {
                    var a = s.addresses[i];
                    parts.push(a.street + ' ' + a.zip + ' ' + a.city + ' ' + (a.label || ''));
                }
                parts = parts.concat(s.special_features || []);
                parts = parts.concat(s.languages || []);
                return parts.join(' ').toLowerCase().indexOf(searchQ) !== -1;
            });
        }

        // Style chip filter
        if (state.activeStyleFilter !== 'all') {
            var sf = state.activeStyleFilter.toLowerCase();
            results = results.filter(function (s) {
                for (var i = 0; i < s.styles.length; i++) {
                    if (s.styles[i].toLowerCase().indexOf(sf) !== -1) return true;
                }
                return false;
            });
        }

        // Style dropdown
        var styleVal = $('filterStyle') ? $('filterStyle').value : '';
        if (styleVal) {
            var svl = styleVal.toLowerCase();
            results = results.filter(function (s) {
                for (var i = 0; i < s.styles.length; i++) {
                    if (s.styles[i].toLowerCase().indexOf(svl) !== -1) return true;
                }
                return false;
            });
        }

        // District
        var districtVal = $('filterDistrict') ? $('filterDistrict').value : '';
        if (districtVal) {
            if (districtVal === 'other') {
                results = results.filter(function (s) {
                    for (var i = 0; i < s.addresses.length; i++) {
                        if (!s.addresses[i].zip.match(/^40/)) return true;
                    }
                    return false;
                });
            } else {
                results = results.filter(function (s) {
                    for (var i = 0; i < s.addresses.length; i++) {
                        if (s.addresses[i].zip === districtVal) return true;
                    }
                    return false;
                });
            }
        }

        // Feature
        var featureVal = $('filterFeature') ? $('filterFeature').value : '';
        if (featureVal) {
            results = results.filter(function (s) {
                var feats = (s.special_features || []).join(' ').toLowerCase();
                var stys = s.styles.join(' ').toLowerCase();
                switch (featureVal) {
                    case 'drop_in': return s.drop_in;
                    case 'english': return s.languages && s.languages.indexOf('English') !== -1;
                    case 'prenatal': return /prenatal|schwanger|postnatal|mama/i.test(stys + ' ' + feats);
                    case 'seniors': return /55\+|60\+/i.test(stys + ' ' + feats);
                    case 'kids': return /kids|kinder|family|kleinkind/i.test(stys + ' ' + feats);
                    case 'teacher_training': return /teacher training|ryt/i.test(feats);
                    case 'outdoor': return /outdoor|park|sommer/i.test(feats);
                    default: return true;
                }
            });
        }

        // Sort
        var sortVal = $('filterSort') ? $('filterSort').value : 'name';
        if (sortVal === 'name') {
            results.sort(function (a, b) { return a.name.localeCompare(b.name); });
        } else if (sortVal === 'styles') {
            results.sort(function (a, b) { return b.styles.length - a.styles.length; });
        } else if (sortVal === 'district') {
            results.sort(function (a, b) {
                var za = (a.addresses[0] && a.addresses[0].zip) || 'zzzz';
                var zb = (b.addresses[0] && b.addresses[0].zip) || 'zzzz';
                return za.localeCompare(zb);
            });
        }

        state.filteredStudios = results;
        renderStudios();
        updateFilterCount();
    }

    function filterByStyle(style) {
        state.activeStyleFilter = style;
        var chips = document.querySelectorAll('#quickFilters .chip');
        for (var i = 0; i < chips.length; i++) {
            if (chips[i].getAttribute('data-filter') === style) {
                chips[i].classList.add('active');
            } else {
                chips[i].classList.remove('active');
            }
        }
        var quickChip = document.querySelector('#quickFilters .chip[data-filter="' + style + '"]');
        if (!quickChip) {
            // Not in quick filters, clear all chips and use dropdown
            for (var j = 0; j < chips.length; j++) chips[j].classList.remove('active');
            if ($('filterStyle')) $('filterStyle').value = style;
        }
        applyFilters();
    }

    function resetFilters() {
        state.searchQuery = '';
        state.activeStyleFilter = 'all';
        if ($('heroSearch')) $('heroSearch').value = '';
        if ($('filterStyle')) $('filterStyle').value = '';
        if ($('filterDistrict')) $('filterDistrict').value = '';
        if ($('filterFeature')) $('filterFeature').value = '';
        if ($('filterSort')) $('filterSort').value = 'name';
        if ($('searchClear')) $('searchClear').style.display = 'none';

        var chips = document.querySelectorAll('#quickFilters .chip');
        for (var i = 0; i < chips.length; i++) {
            if (chips[i].getAttribute('data-filter') === 'all') {
                chips[i].classList.add('active');
            } else {
                chips[i].classList.remove('active');
            }
        }
        applyFilters();
    }

    function updateFilterCount() {
        var count = $('filterCount');
        if (!count) return;
        var active = 0;
        if (state.activeStyleFilter !== 'all') active++;
        if ($('filterStyle') && $('filterStyle').value) active++;
        if ($('filterDistrict') && $('filterDistrict').value) active++;
        if ($('filterFeature') && $('filterFeature').value) active++;
        if (state.searchQuery) active++;
        count.textContent = active;
        count.style.display = active > 0 ? '' : 'none';
    }

    // --- Map ---
    function initMap() {
        if (typeof L === 'undefined') {
            console.log('[YogaBasel] Leaflet not available, skipping map. Will retry in 2s...');
            setTimeout(initMap, 2000);
            return;
        }
        if (state.map) return; // Already initialized

        var mapEl = $('map');
        if (!mapEl) return;

        console.log('[YogaBasel] Initializing map...');
        state.map = L.map('map').setView([47.557, 7.588], 13);

        L.tileLayer('https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png', {
            attribution: '&copy; <a href="https://www.openstreetmap.org/copyright">OpenStreetMap</a>',
            maxZoom: 18
        }).addTo(state.map);

        var yogaIcon = L.divIcon({
            html: '<div style="background:#6B5B95;color:white;width:28px;height:28px;border-radius:50%;display:flex;align-items:center;justify-content:center;font-size:14px;box-shadow:0 2px 8px rgba(0,0,0,0.3);border:2px solid white;">🧘</div>',
            iconSize: [28, 28],
            iconAnchor: [14, 14],
            className: ''
        });

        for (var i = 0; i < state.studios.length; i++) {
            var studio = state.studios[i];
            if (!studio.lat || !studio.lng) continue;

            var address = studio.addresses[0] || {};
            var addressText = address.street ? address.street + ', ' + (address.zip || '') + ' ' + (address.city || '') : '';
            var popupHtml = '<div style="min-width:200px;">' +
                '<strong style="font-size:14px;">' + escapeHtml(studio.name) + '</strong><br>' +
                '<span style="font-size:12px;color:#666;">' + escapeHtml(addressText) + '</span><br>' +
                '<span style="font-size:11px;color:#6B5B95;">' + studio.styles.slice(0, 3).join(', ') + (studio.styles.length > 3 ? '...' : '') + '</span><br>' +
                (studio.website ? '<a href="' + escapeHtml(studio.website) + '" target="_blank" rel="noopener" style="font-size:12px;">Website &rarr;</a>' : '') +
                '</div>';

            L.marker([studio.lat, studio.lng], { icon: yogaIcon })
                .addTo(state.map)
                .bindPopup(popupHtml);
        }
    }

    // --- PDF Export ---
    function exportPDF() {
        if (typeof window.jspdf === 'undefined') {
            alert('PDF-Bibliothek wird noch geladen. Bitte versuche es in ein paar Sekunden nochmal.');
            return;
        }

        var jsPDF = window.jspdf.jsPDF;
        var doc = new jsPDF('p', 'mm', 'a4');
        var pageWidth = doc.internal.pageSize.getWidth();
        var locale = state.lang === 'de' ? 'de-CH' : 'en-GB';
        var now = new Date().toLocaleDateString(locale);

        doc.setFontSize(22);
        doc.setFont('helvetica', 'bold');
        doc.text(t('pdf.title'), pageWidth / 2, 20, { align: 'center' });

        doc.setFontSize(10);
        doc.setFont('helvetica', 'normal');
        doc.setTextColor(100);
        doc.text(t('pdf.generated') + ' ' + now + ' | yogakursebasel.ch', pageWidth / 2, 28, { align: 'center' });
        doc.setTextColor(0);

        var tableData = [];
        for (var i = 0; i < state.filteredStudios.length; i++) {
            var s = state.filteredStudios[i];
            var addr = s.addresses[0] || {};
            tableData.push([
                s.name,
                addr.street ? addr.street + ', ' + (addr.zip || '') + ' ' + (addr.city || '') : '',
                s.styles.join(', '),
                s.teachers.join(', ') || '-',
                s.website || '-'
            ]);
        }

        doc.autoTable({
            startY: 35,
            head: [['Studio', state.lang === 'de' ? 'Adresse' : 'Address', state.lang === 'de' ? 'Stile' : 'Styles', state.lang === 'de' ? 'Lehrer/innen' : 'Teachers', 'Website']],
            body: tableData,
            styles: { fontSize: 7, cellPadding: 2, overflow: 'linebreak', lineWidth: 0.1 },
            headStyles: { fillColor: [107, 91, 149], textColor: 255, fontStyle: 'bold', fontSize: 8 },
            alternateRowStyles: { fillColor: [248, 246, 252] },
            columnStyles: {
                0: { cellWidth: 30, fontStyle: 'bold' },
                1: { cellWidth: 35 },
                2: { cellWidth: 50 },
                3: { cellWidth: 30 },
                4: { cellWidth: 40 }
            },
            margin: { left: 10, right: 10 }
        });

        doc.save('yoga-studios-basel-' + now.replace(/\./g, '-') + '.pdf');
    }

    // --- Theme ---
    function applyTheme() {
        document.documentElement.setAttribute('data-theme', state.theme);
    }

    function toggleTheme() {
        state.theme = state.theme === 'light' ? 'dark' : 'light';
        try { localStorage.setItem('yogabasel-theme', state.theme); } catch (e) {}
        applyTheme();
    }

    // --- Language ---
    function applyLanguage() {
        var langLabel = $('langLabel');
        if (langLabel) langLabel.textContent = state.lang.toUpperCase();

        var els = document.querySelectorAll('[data-i18n]');
        for (var i = 0; i < els.length; i++) {
            var key = els[i].getAttribute('data-i18n');
            var val = t(key);
            if (val && val !== key) els[i].innerHTML = val;
        }

        var placeholders = document.querySelectorAll('[data-i18n-placeholder]');
        for (var j = 0; j < placeholders.length; j++) {
            var pkey = placeholders[j].getAttribute('data-i18n-placeholder');
            var pval = t(pkey);
            if (pval && pval !== pkey) placeholders[j].placeholder = pval;
        }

        document.documentElement.lang = state.lang;
    }

    function toggleLanguage() {
        state.lang = state.lang === 'de' ? 'en' : 'de';
        try { localStorage.setItem('yogabasel-lang', state.lang); } catch (e) {}
        applyLanguage();
        renderStudios();
        renderStylesOverview();
    }

    // --- Last Updated ---
    function updateLastUpdated() {
        var el = $('lastUpdated');
        if (!el) return;
        var now = new Date();
        el.textContent = now.toLocaleDateString(state.lang === 'de' ? 'de-CH' : 'en-GB') + ' ' +
            now.toLocaleTimeString(state.lang === 'de' ? 'de-CH' : 'en-GB', { hour: '2-digit', minute: '2-digit' });
        el.setAttribute('datetime', now.toISOString());
        var yearEl = $('currentYear');
        if (yearEl) yearEl.textContent = now.getFullYear();
    }

    // --- Event Listeners ---
    function setupEventListeners() {
        // Theme toggle
        var themeBtn = $('themeToggle');
        if (themeBtn) themeBtn.addEventListener('click', toggleTheme);

        // Language toggle
        var langBtn = $('langToggle');
        if (langBtn) langBtn.addEventListener('click', toggleLanguage);

        // Mobile menu
        var menuToggle = $('menuToggle');
        var nav = $('nav');
        if (menuToggle && nav) {
            menuToggle.addEventListener('click', function () {
                var open = menuToggle.getAttribute('aria-expanded') === 'true';
                menuToggle.setAttribute('aria-expanded', String(!open));
                nav.classList.toggle('open');
            });
            var navLinks = nav.querySelectorAll('.nav-link');
            for (var i = 0; i < navLinks.length; i++) {
                navLinks[i].addEventListener('click', function () {
                    menuToggle.setAttribute('aria-expanded', 'false');
                    nav.classList.remove('open');
                });
            }
        }

        // Search
        var searchInput = $('heroSearch');
        var searchClear = $('searchClear');
        var searchTimer = null;
        if (searchInput) {
            searchInput.addEventListener('input', function () {
                clearTimeout(searchTimer);
                searchTimer = setTimeout(function () {
                    state.searchQuery = searchInput.value;
                    if (searchClear) searchClear.style.display = searchInput.value ? '' : 'none';
                    applyFilters();
                }, 200);
            });
        }
        if (searchClear) {
            searchClear.addEventListener('click', function () {
                if (searchInput) searchInput.value = '';
                state.searchQuery = '';
                searchClear.style.display = 'none';
                applyFilters();
                if (searchInput) searchInput.focus();
            });
        }

        // Quick filter chips
        var quickFilters = $('quickFilters');
        if (quickFilters) {
            quickFilters.addEventListener('click', function (e) {
                var chip = e.target.closest ? e.target.closest('.chip') : null;
                if (!chip && e.target.classList.contains('chip')) chip = e.target;
                if (!chip) return;
                var filter = chip.getAttribute('data-filter');
                state.activeStyleFilter = filter;
                var allChips = quickFilters.querySelectorAll('.chip');
                for (var i = 0; i < allChips.length; i++) allChips[i].classList.remove('active');
                chip.classList.add('active');
                if ($('filterStyle')) $('filterStyle').value = '';
                applyFilters();
            });
        }

        // Filters toggle
        var filtersToggle = $('filtersToggle');
        var filtersPanel = $('filtersPanel');
        if (filtersToggle && filtersPanel) {
            filtersToggle.addEventListener('click', function () {
                var expanded = filtersToggle.getAttribute('aria-expanded') === 'true';
                filtersToggle.setAttribute('aria-expanded', String(!expanded));
                filtersPanel.hidden = expanded;
            });
        }

        // Filter dropdowns
        var filterIds = ['filterStyle', 'filterDistrict', 'filterFeature', 'filterSort'];
        for (var fi = 0; fi < filterIds.length; fi++) {
            var el = $(filterIds[fi]);
            if (el) el.addEventListener('change', applyFilters);
        }

        // Reset filters
        var resetBtn = $('resetFilters');
        if (resetBtn) resetBtn.addEventListener('click', resetFilters);
        var clearBtn = $('clearAllFilters');
        if (clearBtn) clearBtn.addEventListener('click', resetFilters);

        // View toggle
        var gridEl = $('studiosGrid');
        var viewGridBtn = $('viewGrid');
        var viewListBtn = $('viewList');
        if (viewGridBtn && viewListBtn && gridEl) {
            viewGridBtn.addEventListener('click', function () {
                gridEl.classList.remove('list-view');
                viewGridBtn.classList.add('active');
                viewListBtn.classList.remove('active');
            });
            viewListBtn.addEventListener('click', function () {
                gridEl.classList.add('list-view');
                viewListBtn.classList.add('active');
                viewGridBtn.classList.remove('active');
            });
        }

        // PDF export
        var pdfBtn = $('exportPdf');
        if (pdfBtn) pdfBtn.addEventListener('click', exportPDF);

        // Modal
        var modalClose = $('modalClose');
        if (modalClose) modalClose.addEventListener('click', closeModal);
        var modalOverlay = $('modalOverlay');
        if (modalOverlay) {
            modalOverlay.addEventListener('click', function (e) {
                if (e.target === e.currentTarget) closeModal();
            });
        }
        document.addEventListener('keydown', function (e) {
            if (e.key === 'Escape') closeModal();
        });

        // Header scroll
        var header = $('header');
        if (header) {
            window.addEventListener('scroll', function () {
                if (window.scrollY > 10) header.classList.add('scrolled');
                else header.classList.remove('scrolled');
            }, { passive: true });
        }

        // Back to top
        var backToTop = $('backToTop');
        if (backToTop) {
            window.addEventListener('scroll', function () {
                if (window.scrollY > 600) backToTop.classList.add('visible');
                else backToTop.classList.remove('visible');
            }, { passive: true });
            backToTop.addEventListener('click', function () {
                window.scrollTo({ top: 0, behavior: 'smooth' });
            });
        }

        // Style links in footer
        var styleLinks = document.querySelectorAll('[data-style-link]');
        for (var sl = 0; sl < styleLinks.length; sl++) {
            styleLinks[sl].addEventListener('click', (function (link) {
                return function (e) {
                    e.preventDefault();
                    filterByStyle(link.getAttribute('data-style-link'));
                    var studios = $('studios');
                    if (studios) studios.scrollIntoView({ behavior: 'smooth' });
                };
            })(styleLinks[sl]));
        }
    }

})();
