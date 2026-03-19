/* ============================================================
   YOGA KURSE BASEL — Main Application
   ============================================================ */

(function () {
    'use strict';

    // --- i18n translations ---
    const translations = {
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
            'pdf.generated': 'Erstellt am',
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
            'pdf.generated': 'Generated on',
        }
    };

    // --- State ---
    let state = {
        studios: [],
        filteredStudios: [],
        lang: localStorage.getItem('yogabasel-lang') || 'de',
        theme: localStorage.getItem('yogabasel-theme') || 'light',
        view: 'grid',
        activeStyleFilter: 'all',
        searchQuery: '',
        map: null,
        markers: []
    };

    // --- Init ---
    document.addEventListener('DOMContentLoaded', async () => {
        applyTheme();
        applyLanguage();
        await loadData();
        setupEventListeners();
        renderStudios();
        renderStylesOverview();
        initMap();
        updateLastUpdated();
    });

    // --- Data Loading ---
    async function loadData() {
        try {
            const res = await fetch('./data/studios.json');
            const data = await res.json();
            state.studios = data.studios.filter(s => s.active);
            state.filteredStudios = [...state.studios];
            populateStyleFilter(data.styles_index);
            document.getElementById('studioCount').textContent = state.studios.length + '+';
            document.getElementById('totalCount').textContent = state.studios.length;
        } catch (e) {
            console.error('Failed to load studio data:', e);
        }
    }

    function populateStyleFilter(styles) {
        const select = document.getElementById('filterStyle');
        styles.forEach(style => {
            const opt = document.createElement('option');
            opt.value = style;
            opt.textContent = style;
            select.appendChild(opt);
        });
    }

    // --- Rendering ---
    function renderStudios() {
        const grid = document.getElementById('studiosGrid');
        const noResults = document.getElementById('noResults');
        const visibleCount = document.getElementById('visibleCount');

        grid.innerHTML = '';

        if (state.filteredStudios.length === 0) {
            noResults.hidden = false;
            visibleCount.textContent = '0';
            return;
        }

        noResults.hidden = true;
        visibleCount.textContent = state.filteredStudios.length;

        state.filteredStudios.forEach((studio, i) => {
            const card = createStudioCard(studio, i);
            grid.appendChild(card);
        });
    }

    function createStudioCard(studio, index) {
        const card = document.createElement('article');
        card.className = 'studio-card';
        card.setAttribute('data-studio-id', studio.id);
        card.style.animationDelay = `${Math.min(index * 0.03, 0.3)}s`;

        const address = studio.addresses[0];
        const addressText = address ? `${address.street}, ${address.zip} ${address.city}${address.label ? ' — ' + address.label : ''}` : '';

        const maxTags = 4;
        const visibleStyles = studio.styles.slice(0, maxTags);
        const hiddenCount = Math.max(0, studio.styles.length - maxTags);

        const teacherNames = studio.teachers.slice(0, 3).join(', ');
        const t = translations[state.lang];

        card.innerHTML = `
            <div class="studio-card-header">
                <h3 class="studio-name">${escapeHtml(studio.name)}</h3>
                ${studio.drop_in ? `<span class="studio-badge drop-in">Drop-in</span>` : ''}
            </div>
            <div class="studio-address">
                <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M21 10c0 7-9 13-9 13s-9-6-9-13a9 9 0 0 1 18 0z"/><circle cx="12" cy="10" r="3"/></svg>
                <span>${escapeHtml(addressText)}</span>
            </div>
            <p class="studio-description">${escapeHtml(studio.description)}</p>
            <div class="studio-styles">
                ${visibleStyles.map(s => `<span class="style-tag">${escapeHtml(s)}</span>`).join('')}
                ${hiddenCount > 0 ? `<span class="style-tag more">+${hiddenCount} ${t['card.more_styles']}</span>` : ''}
            </div>
            <div class="studio-footer">
                <span class="studio-teachers">
                    ${teacherNames ? `
                        <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M20 21v-2a4 4 0 0 0-4-4H8a4 4 0 0 0-4 4v2"/><circle cx="12" cy="7" r="4"/></svg>
                        ${escapeHtml(teacherNames)}${studio.teachers.length > 3 ? '...' : ''}
                    ` : ''}
                </span>
                <span class="studio-link">${t['card.details']} &rarr;</span>
            </div>
        `;

        card.addEventListener('click', () => openModal(studio));
        return card;
    }

    function renderStylesOverview() {
        const grid = document.getElementById('stylesGrid');
        const styleCounts = {};

        state.studios.forEach(studio => {
            studio.styles.forEach(style => {
                // Normalize style names for counting
                const normalizedStyle = style.replace(/\s*(Yoga|Flow|Led|Mysore)?\s*$/i, '').trim() || style;
                // Use original name for display
                if (!styleCounts[style]) {
                    styleCounts[style] = 0;
                }
                styleCounts[style]++;
            });
        });

        // Sort by count descending
        const sorted = Object.entries(styleCounts).sort((a, b) => b[1] - a[1]);
        const t = translations[state.lang];

        grid.innerHTML = sorted.map(([style, count]) => `
            <div class="style-card" data-style="${escapeHtml(style)}">
                <div class="style-card-name">${escapeHtml(style)}</div>
                <div class="style-card-count">${count} ${t['styles.studios_count']}</div>
            </div>
        `).join('');

        // Click handler
        grid.querySelectorAll('.style-card').forEach(card => {
            card.addEventListener('click', () => {
                const style = card.dataset.style;
                filterByStyle(style);
                document.getElementById('studios').scrollIntoView({ behavior: 'smooth' });
            });
        });
    }

    // --- Modal ---
    function openModal(studio) {
        const overlay = document.getElementById('modalOverlay');
        const content = document.getElementById('modalContent');
        const t = translations[state.lang];

        const addresses = studio.addresses.map(a =>
            `${a.street}, ${a.zip} ${a.city}${a.label ? ' (' + a.label + ')' : ''}`
        ).join('<br>');

        content.innerHTML = `
            <h2 id="modalTitle">${escapeHtml(studio.name)}</h2>

            <div class="modal-section">
                <div class="modal-info-row">
                    <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M21 10c0 7-9 13-9 13s-9-6-9-13a9 9 0 0 1 18 0z"/><circle cx="12" cy="10" r="3"/></svg>
                    <span>${addresses}</span>
                </div>
                ${studio.phone ? `
                <div class="modal-info-row">
                    <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M22 16.92v3a2 2 0 0 1-2.18 2 19.79 19.79 0 0 1-8.63-3.07 19.5 19.5 0 0 1-6-6 19.79 19.79 0 0 1-3.07-8.67A2 2 0 0 1 4.11 2h3a2 2 0 0 1 2 1.72c.127.96.361 1.903.7 2.81a2 2 0 0 1-.45 2.11L8.09 9.91a16 16 0 0 0 6 6l1.27-1.27a2 2 0 0 1 2.11-.45c.907.339 1.85.573 2.81.7A2 2 0 0 1 22 16.92z"/></svg>
                    <a href="tel:${escapeHtml(studio.phone)}">${escapeHtml(studio.phone)}</a>
                </div>` : ''}
                ${studio.email ? `
                <div class="modal-info-row">
                    <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M4 4h16c1.1 0 2 .9 2 2v12c0 1.1-.9 2-2 2H4c-1.1 0-2-.9-2-2V6c0-1.1.9-2 2-2z"/><polyline points="22,6 12,13 2,6"/></svg>
                    <a href="mailto:${escapeHtml(studio.email)}">${escapeHtml(studio.email)}</a>
                </div>` : ''}
                ${studio.hours ? `
                <div class="modal-info-row">
                    <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><circle cx="12" cy="12" r="10"/><polyline points="12 6 12 12 16 14"/></svg>
                    <span>${escapeHtml(studio.hours)}</span>
                </div>` : ''}
                ${studio.booking_platform ? `
                <div class="modal-info-row">
                    <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><rect x="3" y="4" width="18" height="18" rx="2" ry="2"/><line x1="16" y1="2" x2="16" y2="6"/><line x1="8" y1="2" x2="8" y2="6"/><line x1="3" y1="10" x2="21" y2="10"/></svg>
                    <span>${t['modal.booking']}: ${escapeHtml(studio.booking_platform)}</span>
                </div>` : ''}
                ${studio.languages && studio.languages.length > 0 ? `
                <div class="modal-info-row">
                    <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><circle cx="12" cy="12" r="10"/><line x1="2" y1="12" x2="22" y2="12"/><path d="M12 2a15.3 15.3 0 0 1 4 10 15.3 15.3 0 0 1-4 10 15.3 15.3 0 0 1-4-10 15.3 15.3 0 0 1 4-10z"/></svg>
                    <span>${t['modal.languages']}: ${studio.languages.join(', ')}</span>
                </div>` : ''}
            </div>

            <p style="margin-bottom: var(--spacing-lg); color: var(--color-text-secondary); font-size: 14px; line-height: 1.6;">
                ${escapeHtml(studio.description)}
            </p>

            <div class="modal-section">
                <h3>${t['modal.styles']}</h3>
                <div class="modal-styles">
                    ${studio.styles.map(s => `<span class="style-tag">${escapeHtml(s)}</span>`).join('')}
                </div>
            </div>

            ${studio.teachers.length > 0 ? `
            <div class="modal-section">
                <h3>${t['modal.teachers']}</h3>
                <p style="color: var(--color-text-secondary); font-size: 14px;">${studio.teachers.map(t => escapeHtml(t)).join(', ')}</p>
            </div>` : ''}

            ${studio.special_features && studio.special_features.length > 0 ? `
            <div class="modal-section">
                <h3>${t['modal.features']}</h3>
                <div class="modal-features">
                    ${studio.special_features.map(f => `<span class="feature-badge">${escapeHtml(f)}</span>`).join('')}
                </div>
            </div>` : ''}

            <div class="modal-actions">
                ${studio.website ? `<a href="${escapeHtml(studio.website)}" target="_blank" rel="noopener noreferrer" class="btn btn-primary">${t['modal.website']}</a>` : ''}
                ${studio.schedule_url ? `<a href="${escapeHtml(studio.schedule_url)}" target="_blank" rel="noopener noreferrer" class="btn btn-outline">${t['modal.schedule']}</a>` : ''}
            </div>
        `;

        overlay.hidden = false;
        document.body.style.overflow = 'hidden';
    }

    function closeModal() {
        document.getElementById('modalOverlay').hidden = true;
        document.body.style.overflow = '';
    }

    // --- Filtering ---
    function applyFilters() {
        let results = [...state.studios];
        const searchQ = state.searchQuery.toLowerCase().trim();

        // Search
        if (searchQ) {
            results = results.filter(s => {
                const haystack = [
                    s.name,
                    s.description,
                    ...s.styles,
                    ...s.teachers,
                    ...s.addresses.map(a => `${a.street} ${a.zip} ${a.city} ${a.label || ''}`),
                    ...(s.special_features || []),
                    ...(s.languages || [])
                ].join(' ').toLowerCase();
                return haystack.includes(searchQ);
            });
        }

        // Style chip filter
        if (state.activeStyleFilter !== 'all') {
            results = results.filter(s =>
                s.styles.some(style =>
                    style.toLowerCase().includes(state.activeStyleFilter.toLowerCase())
                )
            );
        }

        // Style dropdown
        const styleVal = document.getElementById('filterStyle').value;
        if (styleVal) {
            results = results.filter(s =>
                s.styles.some(style => style.toLowerCase().includes(styleVal.toLowerCase()))
            );
        }

        // District
        const districtVal = document.getElementById('filterDistrict').value;
        if (districtVal) {
            if (districtVal === 'other') {
                results = results.filter(s =>
                    s.addresses.some(a => !a.zip.startsWith('40'))
                );
            } else {
                results = results.filter(s =>
                    s.addresses.some(a => a.zip === districtVal)
                );
            }
        }

        // Feature
        const featureVal = document.getElementById('filterFeature').value;
        if (featureVal) {
            switch (featureVal) {
                case 'drop_in':
                    results = results.filter(s => s.drop_in);
                    break;
                case 'english':
                    results = results.filter(s => s.languages && s.languages.includes('English'));
                    break;
                case 'prenatal':
                    results = results.filter(s =>
                        s.styles.some(st => /prenatal|schwanger|postnatal|mama/i.test(st)) ||
                        (s.special_features || []).some(f => /schwanger|prenatal|postnatal|mama/i.test(f))
                    );
                    break;
                case 'seniors':
                    results = results.filter(s =>
                        s.styles.some(st => /55\+|60\+/i.test(st)) ||
                        (s.special_features || []).some(f => /55\+|60\+/i.test(f))
                    );
                    break;
                case 'kids':
                    results = results.filter(s =>
                        s.styles.some(st => /kids|kinder|family|kleinkind/i.test(st)) ||
                        (s.special_features || []).some(f => /kids|kinder|family/i.test(f))
                    );
                    break;
                case 'teacher_training':
                    results = results.filter(s =>
                        (s.special_features || []).some(f => /teacher training|ryt/i.test(f))
                    );
                    break;
                case 'outdoor':
                    results = results.filter(s =>
                        (s.special_features || []).some(f => /outdoor|park|sommer/i.test(f))
                    );
                    break;
            }
        }

        // Sort
        const sortVal = document.getElementById('filterSort').value;
        switch (sortVal) {
            case 'name':
                results.sort((a, b) => a.name.localeCompare(b.name));
                break;
            case 'styles':
                results.sort((a, b) => b.styles.length - a.styles.length);
                break;
            case 'district':
                results.sort((a, b) => {
                    const za = a.addresses[0]?.zip || 'zzzz';
                    const zb = b.addresses[0]?.zip || 'zzzz';
                    return za.localeCompare(zb);
                });
                break;
        }

        state.filteredStudios = results;
        renderStudios();
        updateFilterCount();
    }

    function filterByStyle(style) {
        state.activeStyleFilter = style;

        // Update chips
        document.querySelectorAll('#quickFilters .chip').forEach(chip => {
            chip.classList.toggle('active', chip.dataset.filter === style);
        });

        // If not in quick filters, activate 'all' chip visually and set dropdown
        const quickChip = document.querySelector(`#quickFilters .chip[data-filter="${style}"]`);
        if (!quickChip) {
            document.querySelectorAll('#quickFilters .chip').forEach(c => c.classList.remove('active'));
            document.getElementById('filterStyle').value = style;
        }

        applyFilters();
    }

    function resetFilters() {
        state.searchQuery = '';
        state.activeStyleFilter = 'all';
        document.getElementById('heroSearch').value = '';
        document.getElementById('filterStyle').value = '';
        document.getElementById('filterDistrict').value = '';
        document.getElementById('filterFeature').value = '';
        document.getElementById('filterSort').value = 'name';
        document.getElementById('searchClear').style.display = 'none';

        document.querySelectorAll('#quickFilters .chip').forEach(chip => {
            chip.classList.toggle('active', chip.dataset.filter === 'all');
        });

        applyFilters();
    }

    function updateFilterCount() {
        const count = document.getElementById('filterCount');
        let active = 0;
        if (state.activeStyleFilter !== 'all') active++;
        if (document.getElementById('filterStyle').value) active++;
        if (document.getElementById('filterDistrict').value) active++;
        if (document.getElementById('filterFeature').value) active++;
        if (state.searchQuery) active++;

        if (active > 0) {
            count.textContent = active;
            count.style.display = '';
        } else {
            count.style.display = 'none';
        }
    }

    // --- Map ---
    function initMap() {
        if (typeof L === 'undefined') return;

        state.map = L.map('map').setView([47.557, 7.588], 13);

        L.tileLayer('https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png', {
            attribution: '&copy; <a href="https://www.openstreetmap.org/copyright">OpenStreetMap</a>',
            maxZoom: 18
        }).addTo(state.map);

        const yogaIcon = L.divIcon({
            html: '<div style="background:#6B5B95;color:white;width:28px;height:28px;border-radius:50%;display:flex;align-items:center;justify-content:center;font-size:14px;box-shadow:0 2px 8px rgba(0,0,0,0.3);border:2px solid white;">🧘</div>',
            iconSize: [28, 28],
            iconAnchor: [14, 14],
            className: ''
        });

        state.studios.forEach(studio => {
            if (!studio.lat || !studio.lng) return;

            const address = studio.addresses[0];
            const addressText = address ? `${address.street}, ${address.zip} ${address.city}` : '';

            const marker = L.marker([studio.lat, studio.lng], { icon: yogaIcon })
                .addTo(state.map)
                .bindPopup(`
                    <div style="font-family:var(--font-sans);min-width:200px;">
                        <strong style="font-size:14px;">${escapeHtml(studio.name)}</strong><br>
                        <span style="font-size:12px;color:#666;">${escapeHtml(addressText)}</span><br>
                        <span style="font-size:11px;color:#6B5B95;">${studio.styles.slice(0, 3).join(', ')}${studio.styles.length > 3 ? '...' : ''}</span><br>
                        ${studio.website ? `<a href="${escapeHtml(studio.website)}" target="_blank" rel="noopener" style="font-size:12px;">Website &rarr;</a>` : ''}
                    </div>
                `);

            state.markers.push({ marker, studio });
        });
    }

    // --- PDF Export ---
    function exportPDF() {
        if (typeof window.jspdf === 'undefined') {
            alert('PDF-Bibliothek wird geladen. Bitte versuche es nochmal.');
            return;
        }

        const { jsPDF } = window.jspdf;
        const doc = new jsPDF('p', 'mm', 'a4');
        const t = translations[state.lang];
        const pageWidth = doc.internal.pageSize.getWidth();
        const now = new Date().toLocaleDateString(state.lang === 'de' ? 'de-CH' : 'en-GB');

        // Title
        doc.setFontSize(22);
        doc.setFont('helvetica', 'bold');
        doc.text(t['pdf.title'], pageWidth / 2, 20, { align: 'center' });

        doc.setFontSize(10);
        doc.setFont('helvetica', 'normal');
        doc.setTextColor(100);
        doc.text(`${t['pdf.generated']} ${now} | yogakursebasel.ch`, pageWidth / 2, 28, { align: 'center' });

        doc.setTextColor(0);

        // Table data
        const tableData = state.filteredStudios.map(s => {
            const addr = s.addresses[0];
            return [
                s.name,
                addr ? `${addr.street}, ${addr.zip} ${addr.city}` : '',
                s.styles.join(', '),
                s.teachers.join(', ') || '-',
                s.website || '-'
            ];
        });

        doc.autoTable({
            startY: 35,
            head: [['Studio', state.lang === 'de' ? 'Adresse' : 'Address', state.lang === 'de' ? 'Stile' : 'Styles', state.lang === 'de' ? 'Lehrer/innen' : 'Teachers', 'Website']],
            body: tableData,
            styles: {
                fontSize: 7,
                cellPadding: 2,
                overflow: 'linebreak',
                lineWidth: 0.1
            },
            headStyles: {
                fillColor: [107, 91, 149],
                textColor: 255,
                fontStyle: 'bold',
                fontSize: 8
            },
            alternateRowStyles: {
                fillColor: [248, 246, 252]
            },
            columnStyles: {
                0: { cellWidth: 30, fontStyle: 'bold' },
                1: { cellWidth: 35 },
                2: { cellWidth: 50 },
                3: { cellWidth: 30 },
                4: { cellWidth: 40 }
            },
            margin: { left: 10, right: 10 },
            didDrawPage: (data) => {
                // Footer on each page
                doc.setFontSize(8);
                doc.setTextColor(150);
                doc.text(
                    'yogakursebasel.ch — ' + t['footer.disclaimer'].substring(0, 80) + '...',
                    pageWidth / 2,
                    doc.internal.pageSize.getHeight() - 8,
                    { align: 'center' }
                );
            }
        });

        doc.save(`yoga-studios-basel-${now.replace(/\./g, '-')}.pdf`);
    }

    // --- Theme ---
    function applyTheme() {
        document.documentElement.setAttribute('data-theme', state.theme);
    }

    function toggleTheme() {
        state.theme = state.theme === 'light' ? 'dark' : 'light';
        localStorage.setItem('yogabasel-theme', state.theme);
        applyTheme();
    }

    // --- Language ---
    function applyLanguage() {
        const t = translations[state.lang];
        document.getElementById('langLabel').textContent = state.lang.toUpperCase();

        document.querySelectorAll('[data-i18n]').forEach(el => {
            const key = el.getAttribute('data-i18n');
            if (t[key]) {
                el.innerHTML = t[key];
            }
        });

        document.querySelectorAll('[data-i18n-placeholder]').forEach(el => {
            const key = el.getAttribute('data-i18n-placeholder');
            if (t[key]) {
                el.placeholder = t[key];
            }
        });

        document.documentElement.lang = state.lang;
    }

    function toggleLanguage() {
        state.lang = state.lang === 'de' ? 'en' : 'de';
        localStorage.setItem('yogabasel-lang', state.lang);
        applyLanguage();
        renderStudios();
        renderStylesOverview();
    }

    // --- Last Updated ---
    function updateLastUpdated() {
        const el = document.getElementById('lastUpdated');
        const now = new Date();
        const formatter = new Intl.DateTimeFormat(state.lang === 'de' ? 'de-CH' : 'en-GB', {
            day: '2-digit',
            month: '2-digit',
            year: 'numeric',
            hour: '2-digit',
            minute: '2-digit'
        });
        el.textContent = formatter.format(now);
        el.setAttribute('datetime', now.toISOString());
        document.getElementById('currentYear').textContent = now.getFullYear();
    }

    // --- Event Listeners ---
    function setupEventListeners() {
        // Theme toggle
        document.getElementById('themeToggle').addEventListener('click', toggleTheme);

        // Language toggle
        document.getElementById('langToggle').addEventListener('click', toggleLanguage);

        // Mobile menu
        const menuToggle = document.getElementById('menuToggle');
        const nav = document.getElementById('nav');
        menuToggle.addEventListener('click', () => {
            const open = menuToggle.getAttribute('aria-expanded') === 'true';
            menuToggle.setAttribute('aria-expanded', !open);
            nav.classList.toggle('open');
        });

        // Close mobile menu on nav link click
        nav.querySelectorAll('.nav-link').forEach(link => {
            link.addEventListener('click', () => {
                menuToggle.setAttribute('aria-expanded', 'false');
                nav.classList.remove('open');
            });
        });

        // Search
        const searchInput = document.getElementById('heroSearch');
        const searchClear = document.getElementById('searchClear');
        let searchDebounce;

        searchInput.addEventListener('input', () => {
            clearTimeout(searchDebounce);
            searchDebounce = setTimeout(() => {
                state.searchQuery = searchInput.value;
                searchClear.style.display = searchInput.value ? '' : 'none';
                applyFilters();
            }, 200);
        });

        searchClear.addEventListener('click', () => {
            searchInput.value = '';
            state.searchQuery = '';
            searchClear.style.display = 'none';
            applyFilters();
            searchInput.focus();
        });

        // Quick filter chips
        document.getElementById('quickFilters').addEventListener('click', (e) => {
            const chip = e.target.closest('.chip');
            if (!chip) return;
            const filter = chip.dataset.filter;
            state.activeStyleFilter = filter;

            document.querySelectorAll('#quickFilters .chip').forEach(c => c.classList.remove('active'));
            chip.classList.add('active');

            // Clear dropdown if using chip
            document.getElementById('filterStyle').value = '';
            applyFilters();
        });

        // Filters toggle
        const filtersToggle = document.getElementById('filtersToggle');
        const filtersPanel = document.getElementById('filtersPanel');
        filtersToggle.addEventListener('click', () => {
            const expanded = filtersToggle.getAttribute('aria-expanded') === 'true';
            filtersToggle.setAttribute('aria-expanded', !expanded);
            filtersPanel.hidden = expanded;
        });

        // Filter dropdowns
        ['filterStyle', 'filterDistrict', 'filterFeature', 'filterSort'].forEach(id => {
            document.getElementById(id).addEventListener('change', applyFilters);
        });

        // Reset filters
        document.getElementById('resetFilters').addEventListener('click', resetFilters);
        document.getElementById('clearAllFilters').addEventListener('click', resetFilters);

        // View toggle
        const grid = document.getElementById('studiosGrid');
        document.getElementById('viewGrid').addEventListener('click', () => {
            grid.classList.remove('list-view');
            document.getElementById('viewGrid').classList.add('active');
            document.getElementById('viewList').classList.remove('active');
            state.view = 'grid';
        });
        document.getElementById('viewList').addEventListener('click', () => {
            grid.classList.add('list-view');
            document.getElementById('viewList').classList.add('active');
            document.getElementById('viewGrid').classList.remove('active');
            state.view = 'list';
        });

        // PDF export
        document.getElementById('exportPdf').addEventListener('click', exportPDF);

        // Modal
        document.getElementById('modalClose').addEventListener('click', closeModal);
        document.getElementById('modalOverlay').addEventListener('click', (e) => {
            if (e.target === e.currentTarget) closeModal();
        });
        document.addEventListener('keydown', (e) => {
            if (e.key === 'Escape') closeModal();
        });

        // Header scroll behavior
        const header = document.getElementById('header');
        window.addEventListener('scroll', () => {
            header.classList.toggle('scrolled', window.scrollY > 10);
        }, { passive: true });

        // Back to top
        const backToTop = document.getElementById('backToTop');
        window.addEventListener('scroll', () => {
            backToTop.classList.toggle('visible', window.scrollY > 600);
        }, { passive: true });
        backToTop.addEventListener('click', () => {
            window.scrollTo({ top: 0, behavior: 'smooth' });
        });

        // Style links in footer
        document.querySelectorAll('[data-style-link]').forEach(link => {
            link.addEventListener('click', (e) => {
                e.preventDefault();
                filterByStyle(link.dataset.styleLink);
                document.getElementById('studios').scrollIntoView({ behavior: 'smooth' });
            });
        });

        // Keyboard: focus search on /
        document.addEventListener('keydown', (e) => {
            if (e.key === '/' && document.activeElement.tagName !== 'INPUT') {
                e.preventDefault();
                searchInput.focus();
            }
        });
    }

    // --- Utilities ---
    function escapeHtml(str) {
        if (!str) return '';
        const div = document.createElement('div');
        div.textContent = str;
        return div.innerHTML;
    }

})();
