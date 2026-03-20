/* ============================================================
   YOGA KURSE BASEL — Main Application
   ============================================================ */

// Register Service Worker for offline support
if ('serviceWorker' in navigator) {
    navigator.serviceWorker.register('./sw.js').catch(function () {});
}

(function () {
    'use strict';

    // --- i18n translations ---
    var translations = {
        de: {
            'nav.studios': 'Studios',
            'nav.styles': 'Yoga-Stile',
            'nav.map': 'Karte',
            'nav.faq': 'FAQ',
            'hero.title': 'Yoga in der Schweiz<br><span class="hero-accent">alle Kurse auf einen Blick</span>',
            'hero.subtitle': '26 Kantone &bull; Hunderte Studios &bull; Täglich aktualisiert',
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
            'nav.schedule': 'Stundenplan',
            'schedule.title': 'Stundenplan — Kurse nach Tag',
            'schedule.subtitle': 'Wähle einen Tag und sieh alle Yoga-Kurse in Basel mit Uhrzeit, Ort und Lehrer/in',
            'schedule.placeholder': 'Wähle einen Wochentag oben, um alle Kurse zu sehen.',
            'schedule.note': '* Stundenpläne von 7 Studios mit verfügbaren Daten. Einige Studios verwenden dynamische Buchungssysteme — besuche deren Website für den aktuellen Plan.',
            'feedback.title': 'Feedback & Vorschläge',
            'feedback.subtitle': 'Hilf uns, diese Seite zu verbessern. Fehlt ein Studio? Stimmt ein Stundenplan nicht? Hast du Ideen?',
            'feedback.type': 'Art des Feedbacks',
            'feedback.select': 'Bitte wählen...',
            'feedback.missing': 'Fehlendes Studio melden',
            'feedback.wrong': 'Falsche Information korrigieren',
            'feedback.suggestion': 'Verbesserungsvorschlag',
            'feedback.other': 'Sonstiges',
            'feedback.name': 'Name (optional)',
            'feedback.message': 'Deine Nachricht',
            'feedback.send': 'Feedback senden',
            'feedback.thanks': 'Vielen Dank für dein Feedback! Wir werden es so schnell wie möglich berücksichtigen.',
            'geo.nearby': 'In der Nähe',
            'canton.select': 'Wähle deinen Kanton:',
            'canton.choose': 'Kanton wählen...'
        },
        en: {
            'nav.studios': 'Studios',
            'nav.styles': 'Yoga Styles',
            'nav.map': 'Map',
            'nav.faq': 'FAQ',
            'hero.title': 'Yoga in Switzerland<br><span class="hero-accent">all classes at a glance</span>',
            'hero.subtitle': '26 Cantons &bull; Hundreds of Studios &bull; Updated Daily',
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
            'nav.schedule': 'Schedule',
            'schedule.title': 'Schedule — Classes by Day',
            'schedule.subtitle': 'Select a day to see all yoga classes in Basel with time, location and teacher',
            'schedule.placeholder': 'Select a day above to see all classes.',
            'schedule.note': '* Schedules from 7 studios with available data. Some studios use dynamic booking systems — visit their website for the current schedule.',
            'feedback.title': 'Feedback & Suggestions',
            'feedback.subtitle': 'Help us improve this site. Is a studio missing? Is a schedule wrong? Got ideas?',
            'feedback.type': 'Type of feedback',
            'feedback.select': 'Please select...',
            'feedback.missing': 'Report missing studio',
            'feedback.wrong': 'Correct wrong information',
            'feedback.suggestion': 'Improvement suggestion',
            'feedback.other': 'Other',
            'feedback.name': 'Name (optional)',
            'feedback.message': 'Your message',
            'feedback.send': 'Send feedback',
            'feedback.thanks': 'Thank you for your feedback! We will consider it as soon as possible.',
            'geo.nearby': 'Nearby',
            'canton.select': 'Choose your canton:',
            'canton.choose': 'Select canton...'
        },
        it: {
            'nav.studios': 'Studi',
            'nav.styles': 'Stili di Yoga',
            'nav.map': 'Mappa',
            'nav.faq': 'FAQ',
            'nav.schedule': 'Orario',
            'hero.title': 'Yoga in Svizzera<br><span class="hero-accent">tutti i corsi a colpo d\'occhio</span>',
            'hero.subtitle': '26 Cantoni &bull; Centinaia di studi &bull; Aggiornato ogni giorno',
            'hero.search_placeholder': 'Cerca studio, stile di yoga o quartiere...',
            'hero.stat_studios': 'Studi',
            'hero.stat_styles': 'Stili di yoga',
            'hero.stat_updates': 'aggiornato ogni giorno',
            'filters.title': 'Filtri',
            'filters.button': 'Filtri e ordinamento',
            'filters.all': 'Tutti',
            'filters.style': 'Stile di yoga',
            'filters.all_styles': 'Tutti gli stili',
            'filters.district': 'Quartiere / Zona',
            'filters.all_districts': 'Tutti i quartieri',
            'filters.surrounding': 'Dintorni',
            'filters.feature': 'Caratteristiche',
            'filters.all_features': 'Tutte',
            'filters.sort': 'Ordinamento',
            'filters.sort_name': 'Nome (A-Z)',
            'filters.sort_styles': 'Numero di stili',
            'filters.sort_district': 'Quartiere',
            'filters.reset': 'Reimposta filtri',
            'filters.clear_all': 'Cancella tutti i filtri',
            'results.showing': 'Mostrati',
            'results.of': 'di',
            'results.studios': 'Studi',
            'results.export_pdf': 'Scarica PDF',
            'results.none_title': 'Nessuno studio trovato',
            'results.none_text': 'Prova con altri filtri o termini di ricerca.',
            'studios.title': 'Studi di yoga a Basilea',
            'styles.title': 'Stili di yoga a Basilea',
            'styles.subtitle': 'Scopri la variet\u00e0 di stili di yoga offerti a Basilea',
            'map.title': 'Studi sulla mappa',
            'map.subtitle': 'Trova studi di yoga vicino a te',
            'faq.title': 'Domande frequenti',
            'footer.desc': 'La panoramica completa e indipendente di tutti i corsi e gli studi di yoga a Basilea e dintorni.',
            'footer.quick_links': 'Link rapidi',
            'footer.popular_styles': 'Stili popolari',
            'footer.booking': 'Piattaforme di prenotazione',
            'footer.disclaimer': 'Questo sito \u00e8 un portale informativo indipendente e non ha alcun legame commerciale con gli studi elencati. Tutte le informazioni provengono da fonti accessibili al pubblico. Per prezzi e orari aggiornati, visita il sito web dello studio corrispondente.',
            'footer.updated': 'Ultimo aggiornamento:',
            'modal.website': 'Vai al sito',
            'modal.schedule': 'Vedi orario',
            'modal.styles': 'Stili di yoga',
            'modal.teachers': 'Insegnanti',
            'modal.features': 'Caratteristiche',
            'modal.contact': 'Contatto',
            'modal.hours': 'Orari di apertura',
            'modal.languages': 'Lingue',
            'modal.booking': 'Prenota tramite',
            'card.teachers': 'Insegnanti',
            'card.more_styles': 'altri',
            'card.details': 'Dettagli',
            'styles.studios_count': 'Studi',
            'pdf.title': 'Studi di yoga a Basilea \u2014 Panoramica',
            'pdf.generated': 'Creato il',
            'schedule.title': 'Orario \u2014 Corsi per giorno',
            'schedule.subtitle': 'Scegli un giorno e scopri tutti i corsi di yoga a Basilea con orario, luogo e insegnante',
            'schedule.placeholder': 'Scegli un giorno della settimana qui sopra per vedere tutti i corsi.',
            'schedule.note': '* Orari di 7 studi con dati disponibili. Alcuni studi utilizzano sistemi di prenotazione dinamici \u2014 visita il loro sito per l\'orario aggiornato.',
            'feedback.title': 'Feedback e suggerimenti',
            'feedback.subtitle': 'Aiutaci a migliorare questo sito. Manca uno studio? Un orario non \u00e8 corretto? Hai idee?',
            'feedback.type': 'Tipo di feedback',
            'feedback.select': 'Seleziona...',
            'feedback.missing': 'Segnala studio mancante',
            'feedback.wrong': 'Correggi informazione errata',
            'feedback.suggestion': 'Suggerimento di miglioramento',
            'feedback.other': 'Altro',
            'feedback.name': 'Nome (opzionale)',
            'feedback.message': 'Il tuo messaggio',
            'feedback.send': 'Invia feedback',
            'feedback.thanks': 'Grazie per il tuo feedback! Lo prenderemo in considerazione al pi\u00f9 presto.'
        },
        fr: {
            'nav.studios': 'Studios',
            'nav.styles': 'Styles de yoga',
            'nav.map': 'Carte',
            'nav.faq': 'FAQ',
            'nav.schedule': 'Horaire',
            'hero.title': 'Yoga en Suisse<br><span class="hero-accent">tous les cours en un coup d\'\u0153il</span>',
            'hero.subtitle': '26 cantons &bull; des centaines de studios &bull; Mis \u00e0 jour quotidiennement',
            'hero.search_placeholder': 'Chercher un studio, un style de yoga ou un quartier...',
            'hero.stat_studios': 'Studios',
            'hero.stat_styles': 'Styles de yoga',
            'hero.stat_updates': 'mis \u00e0 jour quotidiennement',
            'filters.title': 'Filtres',
            'filters.button': 'Filtres et tri',
            'filters.all': 'Tous',
            'filters.style': 'Style de yoga',
            'filters.all_styles': 'Tous les styles',
            'filters.district': 'Quartier / Zone',
            'filters.all_districts': 'Tous les quartiers',
            'filters.surrounding': 'Environs',
            'filters.feature': 'Particularit\u00e9s',
            'filters.all_features': 'Toutes',
            'filters.sort': 'Tri',
            'filters.sort_name': 'Nom (A-Z)',
            'filters.sort_styles': 'Nombre de styles',
            'filters.sort_district': 'Quartier',
            'filters.reset': 'R\u00e9initialiser les filtres',
            'filters.clear_all': 'Effacer tous les filtres',
            'results.showing': 'Affichage de',
            'results.of': 'sur',
            'results.studios': 'Studios',
            'results.export_pdf': 'T\u00e9l\u00e9charger PDF',
            'results.none_title': 'Aucun studio trouv\u00e9',
            'results.none_text': 'Essaie d\'autres filtres ou termes de recherche.',
            'studios.title': 'Studios de yoga \u00e0 B\u00e2le',
            'styles.title': 'Styles de yoga \u00e0 B\u00e2le',
            'styles.subtitle': 'D\u00e9couvre la diversit\u00e9 des styles de yoga propos\u00e9s \u00e0 B\u00e2le',
            'map.title': 'Studios sur la carte',
            'map.subtitle': 'Trouve des studios de yoga pr\u00e8s de chez toi',
            'faq.title': 'Questions fr\u00e9quentes',
            'footer.desc': 'L\'aper\u00e7u complet et ind\u00e9pendant de tous les cours et studios de yoga \u00e0 B\u00e2le et ses environs.',
            'footer.quick_links': 'Acc\u00e8s rapide',
            'footer.popular_styles': 'Styles populaires',
            'footer.booking': 'Plateformes de r\u00e9servation',
            'footer.disclaimer': 'Ce site est un portail d\'information ind\u00e9pendant et n\'a aucun lien commercial avec les studios r\u00e9pertori\u00e9s. Toutes les informations proviennent de sources accessibles au public. Pour les prix et horaires actuels, consulte le site web du studio concern\u00e9.',
            'footer.updated': 'Derni\u00e8re mise \u00e0 jour :',
            'modal.website': 'Vers le site',
            'modal.schedule': 'Voir l\'horaire',
            'modal.styles': 'Styles de yoga',
            'modal.teachers': 'Enseignant(e)s',
            'modal.features': 'Particularit\u00e9s',
            'modal.contact': 'Contact',
            'modal.hours': 'Heures d\'ouverture',
            'modal.languages': 'Langues',
            'modal.booking': 'R\u00e9server via',
            'card.teachers': 'Enseignant(e)s',
            'card.more_styles': 'autres',
            'card.details': 'D\u00e9tails',
            'styles.studios_count': 'Studios',
            'pdf.title': 'Studios de yoga \u00e0 B\u00e2le \u2014 Aper\u00e7u',
            'pdf.generated': 'Cr\u00e9\u00e9 le',
            'schedule.title': 'Horaire \u2014 Cours par jour',
            'schedule.subtitle': 'Choisis un jour et d\u00e9couvre tous les cours de yoga \u00e0 B\u00e2le avec horaire, lieu et enseignant(e)',
            'schedule.placeholder': 'Choisis un jour de la semaine ci-dessus pour voir tous les cours.',
            'schedule.note': '* Horaires de 7 studios avec donn\u00e9es disponibles. Certains studios utilisent des syst\u00e8mes de r\u00e9servation dynamiques \u2014 consulte leur site pour l\'horaire actuel.',
            'feedback.title': 'Feedback et suggestions',
            'feedback.subtitle': 'Aide-nous \u00e0 am\u00e9liorer ce site. Un studio manque ? Un horaire est incorrect ? Tu as des id\u00e9es ?',
            'feedback.type': 'Type de feedback',
            'feedback.select': 'S\u00e9lectionner...',
            'feedback.missing': 'Signaler un studio manquant',
            'feedback.wrong': 'Corriger une information erron\u00e9e',
            'feedback.suggestion': 'Suggestion d\'am\u00e9lioration',
            'feedback.other': 'Autre',
            'feedback.name': 'Nom (facultatif)',
            'feedback.message': 'Ton message',
            'feedback.send': 'Envoyer le feedback',
            'feedback.thanks': 'Merci pour ton feedback ! Nous le prendrons en compte d\u00e8s que possible.'
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
        markers: [],
        currentCanton: 'basel-stadt'
    };

    // Canton data file mapping
    var cantonDataFiles = {
        'basel-stadt': { studios: 'studios_basel.json', schedule: 'schedule_basel.json' },
        'zurich': { studios: 'studios_zurich.json', schedule: 'schedule_zurich.json' },
        'bern': { studios: 'studios_bern.json', schedule: 'schedule_bern.json' },
        'luzern': { studios: 'studios_luzern.json', schedule: null },
        'geneve': { studios: 'studios_geneve.json', schedule: null },
        'vaud': { studios: 'studios_vaud.json', schedule: null },
        'aargau': { studios: 'studios_aargau.json', schedule: null },
        'st-gallen': { studios: 'studios_st-gallen.json', schedule: null },
        'solothurn': { studios: 'studios_solothurn.json', schedule: null },
        'thurgau': { studios: 'studios_thurgau.json', schedule: null },
        'basel-landschaft': { studios: 'studios_basel-landschaft.json', schedule: null },
        'graubuenden': { studios: 'studios_graubuenden.json', schedule: null },
        'ticino': { studios: 'studios_ticino.json', schedule: null },
        'valais': { studios: 'studios_valais.json', schedule: null },
        'fribourg': { studios: 'studios_fribourg.json', schedule: null },
        'neuchatel': { studios: 'studios_neuchatel.json', schedule: null },
        'schwyz': { studios: 'studios_schwyz.json', schedule: null },
        'zug': { studios: 'studios_zug.json', schedule: null },
        'schaffhausen': { studios: 'studios_schaffhausen.json', schedule: null },
        'jura': { studios: 'studios_jura.json', schedule: null },
        'appenzell-ar': { studios: 'studios_appenzell-ar.json', schedule: null },
        'appenzell-ir': { studios: 'studios_appenzell-ir.json', schedule: null },
        'glarus': { studios: 'studios_glarus.json', schedule: null },
        'obwalden': { studios: 'studios_obwalden.json', schedule: null },
        'nidwalden': { studios: 'studios_nidwalden.json', schedule: null },
        'uri': { studios: 'studios_uri.json', schedule: null }
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
        console.log('[YogaSchweiz] Initializing...');
        applyTheme();
        applyLanguage();
        setupEventListeners();

        // Load saved canton or default to Basel
        var savedCanton = null;
        try { savedCanton = localStorage.getItem('yogabasel-canton'); } catch (e) {}

        // Check URL hash for canton
        var hash = window.location.hash;
        if (hash && hash.indexOf('#canton/') === 0) {
            savedCanton = hash.replace('#canton/', '');
        }

        var cantonToLoad = savedCanton || 'basel-stadt';
        switchCanton(cantonToLoad);

        updateLastUpdated();
        console.log('[YogaSchweiz] Init complete.');
    }

    // Robust DOM ready detection
    if (document.readyState === 'loading') {
        document.addEventListener('DOMContentLoaded', init);
    } else {
        // DOM already parsed (script loaded with defer or after DOMContentLoaded)
        init();
    }

    // --- Canton Switching ---
    function switchCanton(cantonId) {
        state.currentCanton = cantonId;
        try { localStorage.setItem('yogabasel-canton', cantonId); } catch (e) {}

        // Update select
        var sel = $('cantonSelect');
        if (sel) sel.value = cantonId;

        // Check if we have data for this canton
        var files = cantonDataFiles[cantonId];
        if (!files) {
            // Show coming soon
            showComingSoon(cantonId);
            return;
        }

        // Load canton data
        loadData(files.studios);
        if (files.schedule) {
            loadSchedule(files.schedule);
        } else {
            scheduleData = [];
            var list = $('scheduleList');
            if (list) list.innerHTML = '<p class="schedule-placeholder">' + t('schedule.placeholder') + '</p>';
        }

        // Reset map for new canton
        if (state.map) {
            state.map.remove();
            state.map = null;
        }
        setTimeout(initMap, 500);
    }

    function showComingSoon(cantonId) {
        // Find canton name
        var cantonNames = {
            'zurich': 'Zürich', 'bern': 'Bern', 'luzern': 'Luzern', 'geneve': 'Genf',
            'vaud': 'Waadt', 'aargau': 'Aargau', 'st-gallen': 'St. Gallen', 'solothurn': 'Solothurn',
            'basel-landschaft': 'Basel-Landschaft', 'thurgau': 'Thurgau', 'graubuenden': 'Graubünden',
            'ticino': 'Tessin', 'valais': 'Wallis', 'fribourg': 'Freiburg', 'neuchatel': 'Neuenburg',
            'schwyz': 'Schwyz', 'zug': 'Zug', 'schaffhausen': 'Schaffhausen', 'jura': 'Jura',
            'appenzell-ar': 'Appenzell A.Rh.', 'appenzell-ir': 'Appenzell I.Rh.', 'glarus': 'Glarus',
            'obwalden': 'Obwalden', 'nidwalden': 'Nidwalden', 'uri': 'Uri'
        };
        var name = cantonNames[cantonId] || cantonId;

        state.studios = [];
        state.filteredStudios = [];
        var grid = $('studiosGrid');
        if (grid) {
            grid.innerHTML = '<div class="canton-coming-soon" style="grid-column:1/-1">' +
                '<h3>' + escapeHtml(name) + '</h3>' +
                '<p>' + (state.lang === 'de' ? 'Daten für diesen Kanton werden gerade gesammelt. Bald verfügbar!' :
                    state.lang === 'en' ? 'Data for this canton is being collected. Coming soon!' :
                    state.lang === 'it' ? 'I dati per questo cantone sono in fase di raccolta. Disponibili presto!' :
                    'Les données pour ce canton sont en cours de collecte. Bientôt disponible !') + '</p>' +
                '</div>';
        }
        if ($('visibleCount')) $('visibleCount').textContent = '0';
        if ($('totalCount')) $('totalCount').textContent = '0';

        var stylesGrid = $('stylesGrid');
        if (stylesGrid) stylesGrid.innerHTML = '';
        scheduleData = [];
        var schedList = $('scheduleList');
        if (schedList) schedList.innerHTML = '';
    }

    // --- Data Loading ---
    function loadData(fileName) {
        fileName = fileName || 'studios_basel.json';
        var dataUrl = './data/' + fileName;
        console.log('[YogaSchweiz] Fetching data from:', dataUrl);

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
                    console.log('[YogaSchweiz] Loaded', state.studios.length, 'studios for', state.currentCanton);
                    renderStudios();
                    renderStylesOverview();
                    renderGuideStats();
                    renderGuideTable();
                    updateCantonTitles();
                    // Schedule only loaded from switchCanton
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
                '<span class="studio-card-actions">' +
                    '<button class="fav-btn" data-fav="' + escapeHtml(studio.id) + '" title="Favorit">' + (isFavorite(studio.id) ? '\u2605' : '\u2606') + '</button>' +
                    '<button class="share-btn" data-share="' + escapeHtml(studio.id) + '" title="Teilen">\u21AA</button>' +
                '</span>' +
                '<span class="studio-link">' + t('card.details') + ' &rarr;</span>' +
            '</div>';

        // Fav/Share buttons (stop propagation so card click doesn't fire)
        var favBtn = card.querySelector('.fav-btn');
        if (favBtn) favBtn.addEventListener('click', (function (s) {
            return function (ev) { ev.stopPropagation(); toggleFavorite(s.id, ev.target); };
        })(studio));
        var shareBtn = card.querySelector('.share-btn');
        if (shareBtn) shareBtn.addEventListener('click', (function (s) {
            return function (ev) { ev.stopPropagation(); shareStudio(s); };
        })(studio));

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
        // Re-render schedule with current filters
        var activeDay = document.querySelector('#scheduleDays .day-btn.active');
        if (activeDay) {
            renderSchedule(activeDay.getAttribute('data-day'));
        }
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

    // --- Canton-aware Guide Content ---
    function getCantonDisplayName() {
        var names = {
            'basel-stadt': 'Basel', 'zurich': 'Zürich', 'bern': 'Bern', 'luzern': 'Luzern',
            'geneve': 'Genf', 'vaud': 'Waadt', 'aargau': 'Aargau', 'st-gallen': 'St. Gallen',
            'solothurn': 'Solothurn', 'thurgau': 'Thurgau', 'basel-landschaft': 'Basel-Landschaft',
            'graubuenden': 'Graubünden', 'ticino': 'Tessin', 'valais': 'Wallis',
            'fribourg': 'Freiburg', 'neuchatel': 'Neuenburg', 'schwyz': 'Schwyz', 'zug': 'Zug',
            'schaffhausen': 'Schaffhausen', 'jura': 'Jura', 'appenzell-ar': 'Appenzell A.Rh.',
            'appenzell-ir': 'Appenzell I.Rh.', 'glarus': 'Glarus', 'obwalden': 'Obwalden',
            'nidwalden': 'Nidwalden', 'uri': 'Uri'
        };
        return names[state.currentCanton] || state.currentCanton;
    }

    function updateCantonTitles() {
        var name = getCantonDisplayName();
        var stTitle = $('guideTitle');
        if (stTitle) stTitle.textContent = 'Yoga Guide ' + name;

        // Update studios section title
        var studiosTitle = document.querySelector('#studios .section-title');
        if (studiosTitle) studiosTitle.textContent = (state.lang === 'de' ? 'Yoga-Studios in ' : state.lang === 'en' ? 'Yoga Studios in ' : state.lang === 'it' ? 'Studi di yoga a ' : 'Studios de yoga à ') + name;

        // Update styles section title
        var stylesTitle = document.querySelector('#stile .section-title');
        if (stylesTitle) stylesTitle.textContent = (state.lang === 'de' ? 'Yoga-Stile in ' : state.lang === 'en' ? 'Yoga Styles in ' : state.lang === 'it' ? 'Stili di yoga a ' : 'Styles de yoga à ') + name;

        // Update map title
        var mapTitle = document.querySelector('#karte .section-title');
        if (mapTitle) mapTitle.textContent = (state.lang === 'de' ? 'Studios auf der Karte — ' : state.lang === 'en' ? 'Studios on the Map — ' : state.lang === 'it' ? 'Studi sulla mappa — ' : 'Studios sur la carte — ') + name;
    }

    function renderGuideStats() {
        var el = $('guideStats');
        if (!el) return;
        var count = state.studios.length;
        var name = getCantonDisplayName();

        // Count unique styles
        var stylesSet = {};
        var dropInCount = 0;
        for (var i = 0; i < state.studios.length; i++) {
            var s = state.studios[i];
            if (s.drop_in) dropInCount++;
            for (var j = 0; j < s.styles.length; j++) {
                stylesSet[s.styles[j]] = true;
            }
        }
        var styleCount = 0;
        for (var k in stylesSet) { if (stylesSet.hasOwnProperty(k)) styleCount++; }

        el.innerHTML =
            '<div class="guide-stat-card"><div class="guide-stat-number">' + count + '</div><div class="guide-stat-label">Yoga-Studios in ' + escapeHtml(name) + '</div></div>' +
            '<div class="guide-stat-card"><div class="guide-stat-number">' + styleCount + '</div><div class="guide-stat-label">' + (state.lang === 'de' ? 'Verschiedene Yoga-Stile' : state.lang === 'en' ? 'Different Yoga Styles' : state.lang === 'it' ? 'Stili di yoga diversi' : 'Styles de yoga différents') + '</div></div>' +
            '<div class="guide-stat-card"><div class="guide-stat-number">' + dropInCount + '</div><div class="guide-stat-label">Drop-in Studios</div></div>' +
            '<div class="guide-stat-card"><div class="guide-stat-number">CHF 25</div><div class="guide-stat-label">' + (state.lang === 'de' ? 'Drop-in ab diesem Preis' : state.lang === 'en' ? 'Drop-in from this price' : state.lang === 'it' ? 'Drop-in da questo prezzo' : 'Drop-in à partir de ce prix') + '</div></div>';
    }

    function renderGuideTable() {
        var el = $('guideTable');
        if (!el) return;
        if (state.studios.length === 0) {
            el.innerHTML = '';
            return;
        }

        // Sort by number of styles descending, take top 10
        var sorted = state.studios.slice().sort(function (a, b) { return b.styles.length - a.styles.length; });
        var top = sorted.slice(0, Math.min(10, sorted.length));

        var html = '<table><thead><tr>' +
            '<th>Studio</th>' +
            '<th>' + (state.lang === 'de' ? 'Ort' : state.lang === 'en' ? 'Location' : state.lang === 'it' ? 'Luogo' : 'Lieu') + '</th>' +
            '<th>' + (state.lang === 'de' ? 'Stile' : 'Styles') + '</th>' +
            '<th>Drop-in</th>' +
            '<th>' + (state.lang === 'de' ? 'Sprachen' : state.lang === 'en' ? 'Languages' : state.lang === 'it' ? 'Lingue' : 'Langues') + '</th>' +
            '</tr></thead><tbody>';

        for (var i = 0; i < top.length; i++) {
            var s = top[i];
            var city = s.addresses[0] ? s.addresses[0].city : '';
            var langs = (s.languages || []).join(', ');
            var dropIn = s.drop_in ? (state.lang === 'de' ? 'Ja' : state.lang === 'en' ? 'Yes' : state.lang === 'it' ? 'Sì' : 'Oui') : (state.lang === 'de' ? 'Nein' : 'No');
            html += '<tr><td>' + escapeHtml(s.name) + '</td><td>' + escapeHtml(city) + '</td><td>' + s.styles.length + '</td><td>' + dropIn + '</td><td>' + escapeHtml(langs) + '</td></tr>';
        }

        html += '</tbody></table>';
        el.innerHTML = html;
    }

    // --- Schedule ---
    var scheduleData = [];

    function loadSchedule(fileName) {
        fileName = fileName || 'schedule_basel.json';
        var xhr = new XMLHttpRequest();
        xhr.open('GET', './data/' + fileName, true);
        xhr.onreadystatechange = function () {
            if (xhr.readyState !== 4) return;
            if (xhr.status === 200) {
                try {
                    var data = JSON.parse(xhr.responseText);
                    scheduleData = data.classes || [];
                    console.log('[YogaBasel] Loaded', scheduleData.length, 'classes');
                    // Auto-select today's day
                    var days = ['Sunday', 'Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday', 'Saturday'];
                    var today = days[new Date().getDay()];
                    selectDay(today);
                } catch (e) {
                    console.error('[YogaBasel] Error parsing schedule:', e);
                }
            }
        };
        xhr.send();
    }

    function selectDay(day) {
        // Update buttons
        var btns = document.querySelectorAll('#scheduleDays .day-btn');
        for (var i = 0; i < btns.length; i++) {
            if (btns[i].getAttribute('data-day') === day) {
                btns[i].classList.add('active');
            } else {
                btns[i].classList.remove('active');
            }
        }
        renderSchedule(day);
    }

    function renderSchedule(day) {
        var list = $('scheduleList');
        var info = $('scheduleInfo');
        if (!list) return;

        // Get the set of filtered studio IDs
        var filteredIds = {};
        for (var fi = 0; fi < state.filteredStudios.length; fi++) {
            filteredIds[state.filteredStudios[fi].id] = true;
        }

        var searchQ = state.searchQuery.toLowerCase().trim();
        var styleFilter = state.activeStyleFilter;
        var styleDropdown = $('filterStyle') ? $('filterStyle').value : '';

        // Filter classes for this day + active filters
        var classes = [];
        for (var i = 0; i < scheduleData.length; i++) {
            var c = scheduleData[i];
            if (c.day !== day) continue;

            // Filter by studio (must be in filtered studios list if district/feature filters active)
            var districtVal = $('filterDistrict') ? $('filterDistrict').value : '';
            var featureVal = $('filterFeature') ? $('filterFeature').value : '';
            if ((districtVal || featureVal) && !filteredIds[c.studio_id]) continue;

            // Filter by style chip
            if (styleFilter !== 'all') {
                if (c.class_name.toLowerCase().indexOf(styleFilter.toLowerCase()) === -1) continue;
            }

            // Filter by style dropdown
            if (styleDropdown) {
                if (c.class_name.toLowerCase().indexOf(styleDropdown.toLowerCase()) === -1) continue;
            }

            // Filter by search
            if (searchQ) {
                var haystack = [c.class_name, c.studio_name, c.teacher || '', c.level || ''].join(' ').toLowerCase();
                if (haystack.indexOf(searchQ) === -1) continue;
            }

            classes.push(c);
        }

        // Sort by time
        classes.sort(function (a, b) {
            return a.time_start.localeCompare(b.time_start);
        });

        if (classes.length === 0) {
            list.innerHTML = '<p class="schedule-placeholder">' +
                (state.lang === 'de' ? 'Keine Kurse für diesen Tag in unserer Datenbank.' : 'No classes for this day in our database.') +
                '</p>';
            if (info) info.style.display = 'none';
            return;
        }

        // Day names for display
        var dayNames = {
            de: { Monday: 'Montag', Tuesday: 'Dienstag', Wednesday: 'Mittwoch', Thursday: 'Donnerstag', Friday: 'Freitag', Saturday: 'Samstag', Sunday: 'Sonntag' },
            en: { Monday: 'Monday', Tuesday: 'Tuesday', Wednesday: 'Wednesday', Thursday: 'Thursday', Friday: 'Friday', Saturday: 'Saturday', Sunday: 'Sunday' },
            it: { Monday: 'Luned\u00ec', Tuesday: 'Marted\u00ec', Wednesday: 'Mercoled\u00ec', Thursday: 'Gioved\u00ec', Friday: 'Venerd\u00ec', Saturday: 'Sabato', Sunday: 'Domenica' },
            fr: { Monday: 'Lundi', Tuesday: 'Mardi', Wednesday: 'Mercredi', Thursday: 'Jeudi', Friday: 'Vendredi', Saturday: 'Samedi', Sunday: 'Dimanche' }
        };

        if (info) {
            info.style.display = '';
            var countEl = $('scheduleCount');
            if (countEl) {
                var dayName = (dayNames[state.lang] || dayNames.de)[day] || day;
                countEl.textContent = classes.length + ' ' + (state.lang === 'de' ? 'Kurse am' : 'classes on') + ' ' + dayName;
            }
        }

        var html = '<div class="schedule-header">' +
            '<span>' + (state.lang === 'de' ? 'Zeit' : 'Time') + '</span>' +
            '<span>' + (state.lang === 'de' ? 'Kurs' : 'Class') + '</span>' +
            '<span>Studio</span>' +
            '<span>' + (state.lang === 'de' ? 'Lehrer/in' : 'Teacher') + '</span>' +
            '<span>Level</span>' +
            '</div>';

        for (var j = 0; j < classes.length; j++) {
            var c = classes[j];
            var timeStr = c.time_start + (c.time_end ? ' – ' + c.time_end : '');
            var levelText = c.level || '';
            if (levelText === 'all') levelText = state.lang === 'de' ? 'Alle Stufen' : 'All levels';

            html += '<div class="schedule-row">' +
                '<span class="schedule-time">' + escapeHtml(timeStr) + '</span>' +
                '<span class="schedule-class">' + escapeHtml(c.class_name) + '</span>' +
                '<span class="schedule-studio">' + escapeHtml(c.studio_name) + '</span>' +
                '<span class="schedule-teacher">' + escapeHtml(c.teacher || '\u2014') + '</span>' +
                '<span class="schedule-level">' + escapeHtml(levelText) + '</span>' +
                '<button class="schedule-cal-btn" data-cal="' + j + '" title="' + (state.lang === 'de' ? 'Zum Kalender hinzufügen' : 'Add to calendar') + '">\uD83D\uDCC5</button>' +
                '</div>';
        }

        list.innerHTML = html;

        // Calendar button handlers
        var calBtns = list.querySelectorAll('.schedule-cal-btn');
        for (var cb = 0; cb < calBtns.length; cb++) {
            calBtns[cb].addEventListener('click', (function (cls, dy) {
                return function () { addToCalendar(cls.class_name, cls.studio_name, dy, cls.time_start, cls.time_end); };
            })(classes[parseInt(calBtns[cb].getAttribute('data-cal'), 10)], day));
        }
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

        console.log('[YogaSchweiz] Initializing map...');
        var cantonCenters = {
            'basel-stadt': [47.557, 7.588, 13], 'zurich': [47.377, 8.542, 12], 'bern': [46.948, 7.447, 12],
            'luzern': [47.050, 8.305, 12], 'geneve': [46.204, 6.143, 12], 'vaud': [46.520, 6.633, 10],
            'aargau': [47.390, 8.045, 11], 'st-gallen': [47.423, 9.376, 11], 'solothurn': [47.208, 7.537, 11],
            'thurgau': [47.554, 9.085, 11], 'basel-landschaft': [47.484, 7.730, 12], 'graubuenden': [46.850, 9.530, 9],
            'ticino': [46.200, 8.950, 10], 'valais': [46.232, 7.360, 10], 'fribourg': [46.806, 7.162, 11],
            'neuchatel': [46.993, 6.931, 11], 'schwyz': [47.020, 8.653, 11], 'zug': [47.172, 8.517, 12],
            'schaffhausen': [47.696, 8.634, 12], 'jura': [47.365, 7.345, 11], 'appenzell-ar': [47.383, 9.278, 12],
            'appenzell-ir': [47.332, 9.408, 12], 'glarus': [47.040, 9.068, 11], 'obwalden': [46.896, 8.246, 11],
            'nidwalden': [46.948, 8.366, 12], 'uri': [46.880, 8.644, 10]
        };
        var center = cantonCenters[state.currentCanton] || [46.8, 8.2, 8];
        state.map = L.map('map').setView([center[0], center[1]], center[2]);

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

        // Update day button labels
        var dayShort = {
            de: { Monday: 'Mo', Tuesday: 'Di', Wednesday: 'Mi', Thursday: 'Do', Friday: 'Fr', Saturday: 'Sa', Sunday: 'So' },
            en: { Monday: 'Mon', Tuesday: 'Tue', Wednesday: 'Wed', Thursday: 'Thu', Friday: 'Fri', Saturday: 'Sat', Sunday: 'Sun' },
            it: { Monday: 'Lun', Tuesday: 'Mar', Wednesday: 'Mer', Thursday: 'Gio', Friday: 'Ven', Saturday: 'Sab', Sunday: 'Dom' },
            fr: { Monday: 'Lun', Tuesday: 'Mar', Wednesday: 'Mer', Thursday: 'Jeu', Friday: 'Ven', Saturday: 'Sam', Sunday: 'Dim' }
        };
        var dayBtns = document.querySelectorAll('#scheduleDays .day-btn');
        var shorts = dayShort[state.lang] || dayShort.de;
        for (var d = 0; d < dayBtns.length; d++) {
            var dayKey = dayBtns[d].getAttribute('data-day');
            if (shorts[dayKey]) dayBtns[d].textContent = shorts[dayKey];
        }

        document.documentElement.lang = state.lang;
    }

    function toggleLanguage() {
        var langs = ['de', 'en', 'it', 'fr'];
        var idx = langs.indexOf(state.lang);
        state.lang = langs[(idx + 1) % langs.length];
        try { localStorage.setItem('yogabasel-lang', state.lang); } catch (e) {}
        applyLanguage();
        renderStudios();
        renderStylesOverview();
        // Re-render schedule if a day is selected
        var activeDay = document.querySelector('#scheduleDays .day-btn.active');
        if (activeDay) renderSchedule(activeDay.getAttribute('data-day'));
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
        // Canton selector
        var cantonSel = $('cantonSelect');
        if (cantonSel) {
            cantonSel.addEventListener('change', function () {
                if (cantonSel.value) switchCanton(cantonSel.value);
            });
        }

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

        // Feedback form
        var feedbackForm = $('feedbackForm');
        if (feedbackForm) {
            feedbackForm.addEventListener('submit', function (e) {
                e.preventDefault();
                var type = $('feedbackType') ? $('feedbackType').value : '';
                var name = $('feedbackName') ? $('feedbackName').value : '';
                var message = $('feedbackMessage') ? $('feedbackMessage').value : '';
                if (!message.trim()) return;

                // Save feedback locally
                try {
                    var feedbacks = JSON.parse(localStorage.getItem('yogabasel-feedback') || '[]');
                    feedbacks.push({
                        type: type,
                        name: name,
                        message: message,
                        date: new Date().toISOString()
                    });
                    localStorage.setItem('yogabasel-feedback', JSON.stringify(feedbacks));
                } catch (ex) {}

                // Also send via email link as fallback
                var subject = 'YogaBasel Feedback: ' + type;
                var body = 'Typ: ' + type + '\nName: ' + (name || 'Anonym') + '\nNachricht:\n' + message;
                var mailLink = 'mailto:andrea-giovanni@hotmail.com?subject=' + encodeURIComponent(subject) + '&body=' + encodeURIComponent(body);

                // Open mail client
                window.open(mailLink, '_blank');

                // Show success
                feedbackForm.style.display = 'none';
                var success = $('feedbackSuccess');
                if (success) success.style.display = '';
            });
        }

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

        // Schedule day buttons
        var scheduleDays = $('scheduleDays');
        if (scheduleDays) {
            scheduleDays.addEventListener('click', function (e) {
                var btn = e.target;
                if (!btn.classList.contains('day-btn')) return;
                var day = btn.getAttribute('data-day');
                selectDay(day);
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

    // --- Geolocation: Find nearest studios ---
    window.findNearestStudios = findNearestStudios;
    window.promptInstall = promptInstall;

    function findNearestStudios() {
        if (!navigator.geolocation) {
            alert(state.lang === 'de' ? 'Geolocation nicht unterstützt.' : 'Geolocation not supported.');
            return;
        }
        var btn = $('geoBtn');
        if (btn) { btn.disabled = true; btn.textContent = '...'; }

        navigator.geolocation.getCurrentPosition(function (pos) {
            var userLat = pos.coords.latitude;
            var userLng = pos.coords.longitude;
            var withDist = [];
            for (var i = 0; i < state.studios.length; i++) {
                var s = state.studios[i];
                if (!s.lat || !s.lng) continue;
                var dist = Math.sqrt(Math.pow(userLat - s.lat, 2) + Math.pow(userLng - s.lng, 2)) * 111;
                withDist.push({ studio: s, dist: dist });
            }
            withDist.sort(function (a, b) { return a.dist - b.dist; });
            state.filteredStudios = [];
            for (var j = 0; j < withDist.length; j++) state.filteredStudios.push(withDist[j].studio);
            renderStudios();
            if (btn) { btn.disabled = false; btn.textContent = t('geo.nearby'); }
            if (state.map) {
                state.map.setView([userLat, userLng], 14);
                L.circleMarker([userLat, userLng], { radius: 10, color: '#D4A373', fillColor: '#D4A373', fillOpacity: 0.8 })
                    .addTo(state.map).bindPopup(state.lang === 'de' ? 'Dein Standort' : 'Your location');
            }
        }, function () {
            alert(state.lang === 'de' ? 'Standort konnte nicht ermittelt werden.' : 'Could not get location.');
            if (btn) { btn.disabled = false; btn.textContent = t('geo.nearby'); }
        });
    }

    // --- Favorites ---
    function getFavorites() {
        try { return JSON.parse(localStorage.getItem('yogaschweiz-fav') || '[]'); } catch (e) { return []; }
    }
    function toggleFavorite(studioId, el) {
        var favs = getFavorites();
        var idx = favs.indexOf(studioId);
        if (idx === -1) { favs.push(studioId); } else { favs.splice(idx, 1); }
        try { localStorage.setItem('yogaschweiz-fav', JSON.stringify(favs)); } catch (e) {}
        if (el) el.textContent = idx === -1 ? '\u2605' : '\u2606';
    }
    function isFavorite(studioId) { return getFavorites().indexOf(studioId) !== -1; }

    // --- Share ---
    function shareStudio(studio) {
        var text = studio.name + ' \u2014 Yoga in ' + getCantonDisplayName();
        var url = studio.website || window.location.href;
        if (navigator.share) {
            navigator.share({ title: studio.name, text: text, url: url }).catch(function () {});
        } else {
            var ta = document.createElement('textarea');
            ta.value = text + '\n' + url;
            document.body.appendChild(ta); ta.select();
            document.execCommand('copy');
            document.body.removeChild(ta);
            alert(state.lang === 'de' ? 'Link kopiert!' : 'Link copied!');
        }
    }

    // --- Calendar ---
    function addToCalendar(className, studioName, day, timeStart, timeEnd) {
        var dayMap = { Monday: 1, Tuesday: 2, Wednesday: 3, Thursday: 4, Friday: 5, Saturday: 6, Sunday: 0 };
        var now = new Date();
        var diff = (dayMap[day] - now.getDay() + 7) % 7;
        if (diff === 0) diff = 7;
        var d = new Date(now.getTime() + diff * 86400000);
        var sp = timeStart.split(':');
        d.setHours(parseInt(sp[0], 10), parseInt(sp[1], 10), 0, 0);
        var e = new Date(d);
        if (timeEnd) { var ep = timeEnd.split(':'); e.setHours(parseInt(ep[0], 10), parseInt(ep[1], 10), 0, 0); }
        else { e.setHours(e.getHours() + 1); }
        var fmt = function (dt) { return dt.toISOString().replace(/[-:]/g, '').replace(/\.\d{3}/, ''); };
        window.open('https://calendar.google.com/calendar/r/eventedit?text=' +
            encodeURIComponent(className + ' @ ' + studioName) +
            '&dates=' + fmt(d) + '/' + fmt(e) +
            '&details=' + encodeURIComponent('Yoga: ' + className + '\nStudio: ' + studioName) +
            '&location=' + encodeURIComponent(studioName), '_blank');
    }

    // --- PWA Install Prompt ---
    var deferredInstallPrompt = null;
    window.addEventListener('beforeinstallprompt', function (evt) {
        evt.preventDefault();
        deferredInstallPrompt = evt;
        var btn = $('installBtn');
        if (btn) btn.style.display = '';
    });
    function promptInstall() {
        if (deferredInstallPrompt) {
            deferredInstallPrompt.prompt();
            deferredInstallPrompt = null;
        }
    }

    // --- Anonymous Analytics (no cookies, no personal data, GDPR-compliant) ---
    var analytics = {
        startTime: Date.now(),
        clicks: {},
        cantonViews: {},

        // Track anonymous click events via GoatCounter
        trackEvent: function (category, action) {
            var key = category + '/' + action;
            this.clicks[key] = (this.clicks[key] || 0) + 1;
            // Send to GoatCounter as page view event
            if (window.goatcounter && window.goatcounter.count) {
                window.goatcounter.count({ path: '/event/' + key, event: true });
            }
        },

        // Track canton selection
        trackCanton: function (cantonId) {
            this.cantonViews[cantonId] = (this.cantonViews[cantonId] || 0) + 1;
            if (window.goatcounter && window.goatcounter.count) {
                window.goatcounter.count({ path: '/canton/' + cantonId, event: true });
            }
        },

        // Track time on page (send on unload, aggregated)
        trackTimeOnPage: function () {
            var seconds = Math.round((Date.now() - this.startTime) / 1000);
            var bucket;
            if (seconds < 30) bucket = 'under-30s';
            else if (seconds < 60) bucket = '30s-1min';
            else if (seconds < 180) bucket = '1-3min';
            else if (seconds < 300) bucket = '3-5min';
            else if (seconds < 600) bucket = '5-10min';
            else bucket = 'over-10min';
            if (window.goatcounter && window.goatcounter.count) {
                window.goatcounter.count({ path: '/time/' + bucket, event: true });
            }
        }
    };

    // Hook analytics into existing actions

    // Canton switch tracking
    var origSwitchCanton = switchCanton;
    switchCanton = function (cantonId) {
        analytics.trackCanton(cantonId);
        origSwitchCanton(cantonId);
    };
    // Re-expose
    window.findNearestStudios = findNearestStudios;
    window.promptInstall = promptInstall;

    // Track clicks on key buttons
    document.addEventListener('click', function (e) {
        var el = e.target;
        // Studio website click in modal
        if (el.closest && el.closest('.modal-actions .btn-primary')) {
            analytics.trackEvent('click', 'studio-website');
        }
        // Schedule link click in modal
        if (el.closest && el.closest('.modal-actions .btn-outline')) {
            analytics.trackEvent('click', 'studio-schedule');
        }
        // PDF export
        if (el.closest && el.closest('#exportPdf')) {
            analytics.trackEvent('click', 'pdf-export');
        }
        // Geolocation
        if (el.closest && el.closest('#geoBtn')) {
            analytics.trackEvent('click', 'geolocation');
        }
        // Favorite
        if (el.classList && el.classList.contains('fav-btn')) {
            analytics.trackEvent('click', 'favorite');
        }
        // Share
        if (el.classList && el.classList.contains('share-btn')) {
            analytics.trackEvent('click', 'share');
        }
        // Calendar
        if (el.classList && el.classList.contains('schedule-cal-btn')) {
            analytics.trackEvent('click', 'add-calendar');
        }
        // Filter chip
        if (el.closest && el.closest('.chip')) {
            analytics.trackEvent('filter', 'style-chip');
        }
        // Language toggle
        if (el.closest && el.closest('#langToggle')) {
            analytics.trackEvent('click', 'language-' + state.lang);
        }
        // Theme toggle
        if (el.closest && el.closest('#themeToggle')) {
            analytics.trackEvent('click', 'theme-' + state.theme);
        }
    });

    // Track search usage (debounced, only tracks that search was used, not the query)
    var searchTrackTimeout;
    var heroSearchEl = $('heroSearch');
    if (heroSearchEl) {
        heroSearchEl.addEventListener('input', function () {
            clearTimeout(searchTrackTimeout);
            searchTrackTimeout = setTimeout(function () {
                if (heroSearchEl.value.length > 2) {
                    analytics.trackEvent('feature', 'search-used');
                }
            }, 2000);
        });
    }

    // Track time on page when leaving
    window.addEventListener('beforeunload', function () {
        analytics.trackTimeOnPage();
    });
    // Also track via visibilitychange for mobile
    document.addEventListener('visibilitychange', function () {
        if (document.visibilityState === 'hidden') {
            analytics.trackTimeOnPage();
        }
    });

})();
