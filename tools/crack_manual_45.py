#!/usr/bin/env python3
"""
crack_manual_45.py - Manually add verified schedule data for 45 studios.

Data was extracted by visiting each studio's website on 2026-03-25.
Studios where schedule data was found get verified:true entries.
Studios where data could not be extracted are documented with reasons.
"""

import json
import sys
from datetime import datetime, timezone
from pathlib import Path

DATA_DIR = Path(__file__).parent.parent / "data"
TODAY = "2026-03-25"


def make_class(studio_id, studio_name, day, t_start, t_end, class_name, teacher, source, level="all"):
    return {
        "studio_id": studio_id,
        "studio_name": studio_name,
        "day": day,
        "time_start": t_start,
        "time_end": t_end,
        "class_name": class_name,
        "teacher": teacher,
        "level": level,
        "source": source,
        "verified": True,
        "last_checked": TODAY,
    }


# =============================================================================
# HARDCODED SCHEDULE DATA - extracted from websites on 2026-03-25
# =============================================================================

SCHEDULE_DATA = {}

# ---------------------------------------------------------------------------
# BASEL
# ---------------------------------------------------------------------------

# erlenyoga.ch - PRIVATE SITE, login required, no data accessible
# i-yoga-basel.ch - Schedule is in a JPG image (Stundenplan-9_2.jpg), not parseable
# mysorebasel.ch - SSL certificate error, site unreachable
# fitnesspark.ch Basel - Dynamic booking system, schedule not in HTML
# klubschule.ch - National platform, no static Basel yoga schedule

# GYYM Basel - found partial schedule from group fitness page
SCHEDULE_DATA["gyym"] = {
    "canton": "basel",
    "studio_id": "gyym",
    "studio_name": "GYYM Basel",
    "source": "https://gyym.ch/group-fitness/kurse/",
    "classes": [
        make_class("gyym", "GYYM Basel", "Monday", "19:00", "19:50", "Power Yoga", "", "https://gyym.ch/group-fitness/kurse/"),
        make_class("gyym", "GYYM Basel", "Tuesday", "19:35", "20:30", "Power Yoga", "", "https://gyym.ch/group-fitness/kurse/"),
        make_class("gyym", "GYYM Basel", "Wednesday", "19:50", "20:50", "Vinyasa Yoga", "", "https://gyym.ch/group-fitness/kurse/"),
        make_class("gyym", "GYYM Basel", "Friday", "18:00", "19:30", "Inside Flow Yoga", "", "https://gyym.ch/group-fitness/kurse/"),
        make_class("gyym", "GYYM Basel", "Saturday", "11:15", "12:30", "Yoga", "", "https://gyym.ch/group-fitness/kurse/"),
    ]
}

# Sutra House - retreat/event center, no regular weekly yoga classes
# Only hosts retreats and cultural events (music, film, etc.)

# ---------------------------------------------------------------------------
# BASEL-LANDSCHAFT
# ---------------------------------------------------------------------------

# yogashanti.ch - 403 Forbidden, site blocks automated access

# ---------------------------------------------------------------------------
# BERN
# ---------------------------------------------------------------------------

# hothausyoga.com - Uses Momence booking platform, schedule loads dynamically
# origin8.ch - Studio is "auf Pause" (on break), only online classes
# grey-rebel.com - Wix site, schedule loads dynamically via JS

# innerlightacademy.ch - Only offers retreat weeks (e.g. Apr, Aug, Nov 2026), no regular weekly classes

# energieyoga.ch - FOUND FULL SCHEDULE
SCHEDULE_DATA["energie-yoga-bern"] = {
    "canton": "bern",
    "studio_id": "energie-yoga-bern",
    "studio_name": "Energie Yoga",
    "source": "https://energieyoga.ch/b1.html",
    "classes": [
        make_class("energie-yoga-bern", "Energie Yoga", "Monday", "18:45", "19:45", "Energie Yoga", "Cornelia Baer", "https://energieyoga.ch/b1.html"),
        make_class("energie-yoga-bern", "Energie Yoga", "Monday", "20:00", "21:00", "Energie Yoga", "Cornelia Baer", "https://energieyoga.ch/b1.html"),
        make_class("energie-yoga-bern", "Energie Yoga", "Wednesday", "12:15", "13:15", "Schreibtisch Yoga", "Cornelia Baer", "https://energieyoga.ch/b1.html"),
        make_class("energie-yoga-bern", "Energie Yoga", "Wednesday", "18:45", "19:45", "Energie Yoga", "Cornelia Baer", "https://energieyoga.ch/b1.html"),
        make_class("energie-yoga-bern", "Energie Yoga", "Thursday", "12:15", "13:15", "Schreibtisch Yoga", "Cornelia Baer", "https://energieyoga.ch/b1.html"),
    ]
}

# ---------------------------------------------------------------------------
# FRIBOURG
# ---------------------------------------------------------------------------

# sakinayoga.com - Wix site, schedule loads dynamically, no sub-page found
# yoga-nicole.ch - Schedule likely on /kurse but page returned 404

# ---------------------------------------------------------------------------
# GENEVE
# ---------------------------------------------------------------------------

# yoga7.com - Already has 12 verified classes in schedule_geneve.json.
# The /cours-hebdomadaires/ page has schedule but content loads dynamically.
# Existing data is sufficient.

# fancy.yoga - Wix site, all schedule sub-pages return 404
# colife.ch - Already has 21 verified classes in schedule_geneve.json. All good.
# solstudio.ch - Dynamic Healcode booking widget, schedule not in HTML
# swisspilatesandyoga.com - Schedule behind booking system, not extractable
# kastudio.ch - Uses Bsport widget, schedule loads dynamically

# yogasha.ch - Kundalini & Vinyasa in Geneva, all sub-pages 404

# yoga-shambala.ch - FOUND FULL SCHEDULE
SCHEDULE_DATA["yoga-shambala-carouge"] = {
    "canton": "geneve",
    "studio_id": "yoga-shambala-carouge",
    "studio_name": "Yoga Shambala Carouge",
    "source": "https://yoga-shambala.ch/horaires-tarifs.html",
    "classes": [
        make_class("yoga-shambala-carouge", "Yoga Shambala Carouge", "Monday", "12:15", "13:15", "Hatha Yoga", "", "https://yoga-shambala.ch/horaires-tarifs.html"),
        make_class("yoga-shambala-carouge", "Yoga Shambala Carouge", "Monday", "18:15", "19:15", "Hatha Yoga", "", "https://yoga-shambala.ch/horaires-tarifs.html"),
        make_class("yoga-shambala-carouge", "Yoga Shambala Carouge", "Monday", "19:30", "20:30", "Yin Yoga", "", "https://yoga-shambala.ch/horaires-tarifs.html"),
        make_class("yoga-shambala-carouge", "Yoga Shambala Carouge", "Tuesday", "12:15", "13:15", "Hatha Yoga", "", "https://yoga-shambala.ch/horaires-tarifs.html"),
        make_class("yoga-shambala-carouge", "Yoga Shambala Carouge", "Tuesday", "18:15", "19:15", "Hatha Yoga", "", "https://yoga-shambala.ch/horaires-tarifs.html"),
        make_class("yoga-shambala-carouge", "Yoga Shambala Carouge", "Wednesday", "12:15", "13:15", "Hatha Yoga", "", "https://yoga-shambala.ch/horaires-tarifs.html"),
        make_class("yoga-shambala-carouge", "Yoga Shambala Carouge", "Wednesday", "18:15", "19:15", "Hatha Yoga", "", "https://yoga-shambala.ch/horaires-tarifs.html"),
        make_class("yoga-shambala-carouge", "Yoga Shambala Carouge", "Thursday", "12:15", "13:15", "Vinyasa Yoga", "", "https://yoga-shambala.ch/horaires-tarifs.html"),
        make_class("yoga-shambala-carouge", "Yoga Shambala Carouge", "Friday", "12:15", "13:15", "Hatha Yoga", "", "https://yoga-shambala.ch/horaires-tarifs.html"),
        make_class("yoga-shambala-carouge", "Yoga Shambala Carouge", "Saturday", "17:15", "18:15", "Vinyasa Yoga", "", "https://yoga-shambala.ch/horaires-tarifs.html"),
        make_class("yoga-shambala-carouge", "Yoga Shambala Carouge", "Sunday", "10:15", "11:15", "Hatha Yoga", "", "https://yoga-shambala.ch/horaires-tarifs.html"),
    ]
}

# ---------------------------------------------------------------------------
# GRAUBUENDEN
# ---------------------------------------------------------------------------

# belude.ch - FOUND FULL SCHEDULE
SCHEDULE_DATA["belude-yoga-chur"] = {
    "canton": "graubuenden",
    "studio_id": "belude-yoga-chur",
    "studio_name": "Belude Yoga Chur",
    "source": "https://belude.ch/programm.html",
    "classes": [
        make_class("belude-yoga-chur", "Belude Yoga Chur", "Monday", "12:00", "13:00", "Yoga & Klang", "", "https://belude.ch/programm.html"),
        make_class("belude-yoga-chur", "Belude Yoga Chur", "Monday", "18:45", "20:15", "Yoga & Klang", "", "https://belude.ch/programm.html"),
        make_class("belude-yoga-chur", "Belude Yoga Chur", "Tuesday", "09:00", "10:30", "Yoga & Klang", "", "https://belude.ch/programm.html"),
        make_class("belude-yoga-chur", "Belude Yoga Chur", "Tuesday", "18:45", "20:15", "Yoga & Klang", "", "https://belude.ch/programm.html"),
        make_class("belude-yoga-chur", "Belude Yoga Chur", "Wednesday", "06:45", "08:00", "Yoga & Klang", "", "https://belude.ch/programm.html"),
        make_class("belude-yoga-chur", "Belude Yoga Chur", "Wednesday", "17:45", "19:15", "Yoga & Klang", "", "https://belude.ch/programm.html"),
        make_class("belude-yoga-chur", "Belude Yoga Chur", "Thursday", "09:00", "10:30", "Yoga & Klang", "", "https://belude.ch/programm.html"),
        make_class("belude-yoga-chur", "Belude Yoga Chur", "Thursday", "17:45", "19:15", "Yoga & Klang", "", "https://belude.ch/programm.html"),
    ]
}

# yogaplazadavos.ch - FOUND SCHEDULE via MomoYoga
SCHEDULE_DATA["yogaplaza-davos"] = {
    "canton": "graubuenden",
    "studio_id": "yogaplaza-davos",
    "studio_name": "Yoga Plaza Davos",
    "source": "https://www.momoyoga.com/yogaplazadavos/schedule",
    "classes": [
        make_class("yogaplaza-davos", "Yoga Plaza Davos", "Monday", "19:00", "20:30", "Ashtanga Inspired Flow", "Sabine Roder", "https://www.momoyoga.com/yogaplazadavos/schedule"),
        make_class("yogaplaza-davos", "Yoga Plaza Davos", "Wednesday", "09:30", "10:30", "Slow Yoga", "Eva Lutz", "https://www.momoyoga.com/yogaplazadavos/schedule", level="beginner"),
        make_class("yogaplaza-davos", "Yoga Plaza Davos", "Friday", "11:00", "12:00", "Yoga", "Sabine Roder", "https://www.momoyoga.com/yogaplazadavos/schedule"),
        make_class("yogaplaza-davos", "Yoga Plaza Davos", "Saturday", "16:30", "17:30", "Yoga im Waldhotel", "Sabine Roder", "https://www.momoyoga.com/yogaplazadavos/schedule"),
    ]
}

# ---------------------------------------------------------------------------
# JURA
# ---------------------------------------------------------------------------

# pilatesyogajura.com - Wix site, all sub-pages 404, schedule loads dynamically

# ---------------------------------------------------------------------------
# LUZERN
# ---------------------------------------------------------------------------

# ashtanga-luzern.ch - Schedule exists but loads dynamically, teacher is Martyna
# studiofayo.com - Schedule in images (Stundenplan JPGs), not parseable
# pureyouyoga.ch - All sub-pages 404, schedule loads dynamically

# ---------------------------------------------------------------------------
# NEUCHATEL
# ---------------------------------------------------------------------------

# yogashashin.ch - FOUND FULL SCHEDULE via Zenitoo calendar
SCHEDULE_DATA["yoga-shashin-neuchatel"] = {
    "canton": "neuchatel",
    "studio_id": "yoga-shashin-neuchatel",
    "studio_name": "Yoga Shashin Neuchatel",
    "source": "https://yogashashin.zenitoo.ch/fr/calendar",
    "classes": [
        make_class("yoga-shashin-neuchatel", "Yoga Shashin Neuchatel", "Monday", "17:00", "18:05", "Yoga Flow", "Shashin", "https://yogashashin.zenitoo.ch/fr/calendar"),
        make_class("yoga-shashin-neuchatel", "Yoga Shashin Neuchatel", "Monday", "18:15", "19:20", "Yoga Flow", "Shashin", "https://yogashashin.zenitoo.ch/fr/calendar"),
        make_class("yoga-shashin-neuchatel", "Yoga Shashin Neuchatel", "Tuesday", "12:15", "13:20", "Yoga Flow", "Shashin", "https://yogashashin.zenitoo.ch/fr/calendar"),
        make_class("yoga-shashin-neuchatel", "Yoga Shashin Neuchatel", "Tuesday", "17:00", "18:05", "Yoga Flow", "Shashin", "https://yogashashin.zenitoo.ch/fr/calendar"),
        make_class("yoga-shashin-neuchatel", "Yoga Shashin Neuchatel", "Tuesday", "18:30", "19:35", "Yoga Flow", "Shashin", "https://yogashashin.zenitoo.ch/fr/calendar"),
        make_class("yoga-shashin-neuchatel", "Yoga Shashin Neuchatel", "Wednesday", "17:15", "18:20", "Yoga Flow", "Shashin", "https://yogashashin.zenitoo.ch/fr/calendar"),
        make_class("yoga-shashin-neuchatel", "Yoga Shashin Neuchatel", "Wednesday", "18:30", "19:35", "Yoga Flow", "Shashin", "https://yogashashin.zenitoo.ch/fr/calendar"),
        make_class("yoga-shashin-neuchatel", "Yoga Shashin Neuchatel", "Thursday", "17:15", "18:20", "Yoga Flow", "Shashin", "https://yogashashin.zenitoo.ch/fr/calendar"),
        make_class("yoga-shashin-neuchatel", "Yoga Shashin Neuchatel", "Thursday", "18:30", "19:35", "Yoga Flow", "Shashin", "https://yogashashin.zenitoo.ch/fr/calendar"),
        make_class("yoga-shashin-neuchatel", "Yoga Shashin Neuchatel", "Saturday", "09:30", "10:35", "Yoga Flow", "Shashin", "https://yogashashin.zenitoo.ch/fr/calendar"),
    ]
}

# banyann.ch - Wix site, all sub-pages 404
# Already has 1 entry in schedule_neuchatel.json (banyann-yoga)

# ---------------------------------------------------------------------------
# ST-GALLEN
# ---------------------------------------------------------------------------

# poweryogastgallen.com - 403 Forbidden, site blocks automated access

# ---------------------------------------------------------------------------
# VAUD
# ---------------------------------------------------------------------------

# nuevalunayoga.ch - Uses Mindbody booking platform, schedule loads dynamically
# Already has 5 entries in schedule_vaud.json as "nueva-luna"

# theyogarden.ch - Wix site, all sub-pages 404
# Already has 5 entries in schedule_vaud.json as "yogarden"

# yogaflame.ch - Uses Bsport booking widget, schedule not in HTML
# Already has entries in schedule_vaud.json and schedule_geneve.json

# yogavaud.ch - DOMAIN FOR SALE, no active studio

# ashtanga-yoga-lausanne.com - Wix site, schedule page loads dynamically
# Already has 11 entries in schedule_vaud.json as "ashtanga-lausanne"

# yogacenter.ch - Schedule on /cours/ but loads dynamically

# myogastudio.ch - FOUND SCHEDULE
SCHEDULE_DATA["myoga-studio-lausanne"] = {
    "canton": "vaud",
    "studio_id": "myoga-studio-lausanne",
    "studio_name": "Myoga Studio Lausanne",
    "source": "https://myogastudio.ch/classes",
    "classes": [
        make_class("myoga-studio-lausanne", "Myoga Studio Lausanne", "Tuesday", "19:00", "20:15", "Tantra Vinyasa Flow", "", "https://myogastudio.ch/classes", level="1-2"),
        make_class("myoga-studio-lausanne", "Myoga Studio Lausanne", "Wednesday", "20:00", "21:15", "Power Yoga Flow", "", "https://myogastudio.ch/classes", level="1-2"),
    ]
}

# vivre-le-yoga.ch - FOUND FULL SCHEDULE (Yoga Sadhana Lausanne)
SCHEDULE_DATA["yoga-sadhana-lausanne"] = {
    "canton": "vaud",
    "studio_id": "yoga-sadhana-lausanne",
    "studio_name": "Yoga Sadhana Lausanne",
    "source": "https://vivre-le-yoga.ch/cours/plan-des-cours-2/",
    "classes": [
        make_class("yoga-sadhana-lausanne", "Yoga Sadhana Lausanne", "Monday", "19:00", "20:30", "Hatha Yoga", "Maria Rosaria", "https://vivre-le-yoga.ch/cours/plan-des-cours-2/"),
        make_class("yoga-sadhana-lausanne", "Yoga Sadhana Lausanne", "Tuesday", "17:15", "18:45", "Hatha Yoga", "Maria Rosaria", "https://vivre-le-yoga.ch/cours/plan-des-cours-2/"),
        make_class("yoga-sadhana-lausanne", "Yoga Sadhana Lausanne", "Tuesday", "19:00", "21:00", "Hatha Yoga", "Maria Rosaria", "https://vivre-le-yoga.ch/cours/plan-des-cours-2/"),
        make_class("yoga-sadhana-lausanne", "Yoga Sadhana Lausanne", "Wednesday", "09:00", "10:30", "Yoga du matin", "Maria Rosaria", "https://vivre-le-yoga.ch/cours/plan-des-cours-2/"),
        make_class("yoga-sadhana-lausanne", "Yoga Sadhana Lausanne", "Wednesday", "19:00", "20:30", "Hatha Yoga", "Maria Rosaria", "https://vivre-le-yoga.ch/cours/plan-des-cours-2/"),
        make_class("yoga-sadhana-lausanne", "Yoga Sadhana Lausanne", "Thursday", "17:30", "19:00", "Hatha Yoga", "Maria Rosaria", "https://vivre-le-yoga.ch/cours/plan-des-cours-2/"),
    ]
}

# caroledalmas.com - FOUND PARTIAL SCHEDULE (Terre du Yoga Vevey)
SCHEDULE_DATA["terre-du-yoga-vevey"] = {
    "canton": "vaud",
    "studio_id": "terre-du-yoga-vevey",
    "studio_name": "Terre du Yoga Vevey",
    "source": "https://caroledalmas.com/cours-de-yoga/yoga-de-l-energie/",
    "classes": [
        make_class("terre-du-yoga-vevey", "Terre du Yoga Vevey", "Tuesday", "18:30", "19:45", "Yoga sensoriel", "Carole Dalmas", "https://caroledalmas.com/cours-de-yoga/yoga-de-l-energie/"),
        make_class("terre-du-yoga-vevey", "Terre du Yoga Vevey", "Wednesday", "09:15", "10:30", "Yoga sensoriel (Zoom)", "Carole Dalmas", "https://caroledalmas.com/cours-de-yoga/yoga-de-l-energie/"),
        make_class("terre-du-yoga-vevey", "Terre du Yoga Vevey", "Thursday", "09:15", "10:30", "Yoga sensoriel", "Carole Dalmas", "https://caroledalmas.com/cours-de-yoga/yoga-de-l-energie/"),
    ]
}

# ---------------------------------------------------------------------------
# ZURICH
# ---------------------------------------------------------------------------

# soulcity-zurich.ch - Uses Bsport booking widget, schedule loads dynamically
# studioy3.ch - Squarespace dynamic booking, schedule not in HTML
# templeshape.com - Uses Bookee booking system, schedule loads dynamically
# flowfabrik.ch - Wix site, all sub-pages 404

# projectpeace.ch - FOUND DATA (currently only online)
SCHEDULE_DATA["project-peace"] = {
    "canton": "zurich",
    "studio_id": "project-peace",
    "studio_name": "Project Peace",
    "source": "https://projectpeace.ch/yoga-bodywork",
    "classes": [
        make_class("project-peace", "Project Peace", "Tuesday", "20:00", "21:15", "Jivamukti Open Class", "Laurina Wal", "https://projectpeace.ch/yoga-bodywork"),
    ]
}


# =============================================================================
# REPORT: Status of all 45 studios
# =============================================================================

STUDIO_REPORT = [
    # BASEL (7 studios)
    {"studio": "erlenyoga.ch", "canton": "basel", "status": "NOT FOUND",
     "reason": "Site is private, requires login. No public schedule accessible."},
    {"studio": "i-yoga-basel.ch", "canton": "basel", "status": "NOT FOUND",
     "reason": "Schedule is embedded as JPG image (Stundenplan-9_2.jpg), not machine-readable."},
    {"studio": "mysorebasel.ch", "canton": "basel", "status": "NOT FOUND",
     "reason": "SSL certificate error, site unreachable via HTTPS."},
    {"studio": "fitnesspark.ch/basel-heuwaage", "canton": "basel", "status": "NOT FOUND",
     "reason": "Schedule behind dynamic booking system, not in static HTML."},
    {"studio": "gyym.ch", "canton": "basel", "status": "FOUND",
     "reason": "5 yoga classes extracted from group fitness course page.", "classes": 5},
    {"studio": "klubschule.ch", "canton": "basel", "status": "NOT FOUND",
     "reason": "National platform with dynamic course search, no static Basel yoga schedule."},
    {"studio": "sutra-house.com", "canton": "basel", "status": "NOT FOUND",
     "reason": "Retreat/event center only. No regular weekly yoga classes offered."},

    # BASEL-LANDSCHAFT (1 studio)
    {"studio": "yogashanti.ch", "canton": "basel-landschaft", "status": "NOT FOUND",
     "reason": "403 Forbidden - site blocks automated access."},

    # BERN (5 studios)
    {"studio": "hothausyoga.com", "canton": "bern", "status": "NOT FOUND",
     "reason": "Uses Momence booking platform. Schedule loads dynamically via JS."},
    {"studio": "origin8.ch", "canton": "bern", "status": "NOT FOUND",
     "reason": "Studio is 'auf Pause' (on break). Only sporadic online classes."},
    {"studio": "grey-rebel.com", "canton": "bern", "status": "NOT FOUND",
     "reason": "Wix site, schedule loaded dynamically. Sub-pages return 404."},
    {"studio": "innerlightacademy.ch", "canton": "bern", "status": "NOT FOUND",
     "reason": "Only offers multi-day yoga retreat weeks (not regular classes)."},
    {"studio": "energieyoga.ch", "canton": "bern", "status": "FOUND",
     "reason": "5 classes extracted from /b1.html schedule page.", "classes": 5},

    # FRIBOURG (2 studios)
    {"studio": "sakinayoga.com", "canton": "fribourg", "status": "NOT FOUND",
     "reason": "Wix site, schedule loads dynamically. All sub-pages 404."},
    {"studio": "yoga-nicole.ch", "canton": "fribourg", "status": "NOT FOUND",
     "reason": "TriYoga teacher. Schedule page /kurse returned 404."},

    # GENEVE (8 studios)
    {"studio": "yoga7.com", "canton": "geneve", "status": "ALREADY EXISTS",
     "reason": "12 verified classes already in schedule_geneve.json."},
    {"studio": "fancy.yoga", "canton": "geneve", "status": "NOT FOUND",
     "reason": "Wix site, all schedule sub-pages return 404."},
    {"studio": "colife.ch", "canton": "geneve", "status": "ALREADY EXISTS",
     "reason": "21 verified classes already in schedule_geneve.json."},
    {"studio": "solstudio.ch", "canton": "geneve", "status": "NOT FOUND",
     "reason": "Uses Healcode booking widget. Schedule loads dynamically."},
    {"studio": "swisspilatesandyoga.com", "canton": "geneve", "status": "NOT FOUND",
     "reason": "Schedule behind booking system, sub-pages 404."},
    {"studio": "yoga-shambala.ch", "canton": "geneve", "status": "FOUND",
     "reason": "11 classes extracted from /horaires-tarifs.html.", "classes": 11},
    {"studio": "kastudio.ch", "canton": "geneve", "status": "NOT FOUND",
     "reason": "Uses Bsport booking widget. Schedule loads dynamically."},
    {"studio": "yogasha.ch", "canton": "geneve", "status": "NOT FOUND",
     "reason": "Divi/WordPress site. All sub-pages 404."},

    # GRAUBUENDEN (2 studios)
    {"studio": "belude.ch", "canton": "graubuenden", "status": "FOUND",
     "reason": "8 classes extracted from /programm.html.", "classes": 8},
    {"studio": "yogaplazadavos.ch", "canton": "graubuenden", "status": "FOUND",
     "reason": "4 classes extracted via MomoYoga schedule.", "classes": 4},

    # JURA (1 studio)
    {"studio": "pilatesyogajura.com", "canton": "jura", "status": "NOT FOUND",
     "reason": "Wix site, all sub-pages 404. Schedule loads dynamically."},

    # LUZERN (3 studios)
    {"studio": "ashtanga-luzern.ch", "canton": "luzern", "status": "NOT FOUND",
     "reason": "Schedule exists but loads dynamically. Teacher: Martyna."},
    {"studio": "studiofayo.com", "canton": "luzern", "status": "NOT FOUND",
     "reason": "Schedule embedded in JPG images (FAYO_Stundenplan), not parseable."},
    {"studio": "pureyouyoga.ch", "canton": "luzern", "status": "NOT FOUND",
     "reason": "All sub-pages 404. Schedule loads dynamically."},

    # NEUCHATEL (2 studios)
    {"studio": "yogashashin.ch", "canton": "neuchatel", "status": "FOUND",
     "reason": "10 classes extracted via Zenitoo calendar widget.", "classes": 10},
    {"studio": "banyann.ch", "canton": "neuchatel", "status": "ALREADY EXISTS",
     "reason": "1 entry already in schedule_neuchatel.json. Wix site, sub-pages 404."},

    # ST-GALLEN (1 studio)
    {"studio": "poweryogastgallen.com", "canton": "st-gallen", "status": "NOT FOUND",
     "reason": "403 Forbidden - site blocks automated access."},

    # VAUD (9 studios)
    {"studio": "nuevalunayoga.ch", "canton": "vaud", "status": "ALREADY EXISTS",
     "reason": "5 entries already in schedule_vaud.json. Uses Mindbody platform."},
    {"studio": "theyogarden.ch", "canton": "vaud", "status": "ALREADY EXISTS",
     "reason": "5 entries already in schedule_vaud.json. Wix site."},
    {"studio": "yogaflame.ch", "canton": "vaud", "status": "ALREADY EXISTS",
     "reason": "16 entries in schedule_vaud.json + 15 in geneve. Uses Bsport."},
    {"studio": "yogavaud.ch", "canton": "vaud", "status": "NOT FOUND",
     "reason": "Domain is FOR SALE. No active yoga studio."},
    {"studio": "myogastudio.ch", "canton": "vaud", "status": "FOUND",
     "reason": "2 classes extracted from /classes page.", "classes": 2},
    {"studio": "ashtanga-yoga-lausanne.com", "canton": "vaud", "status": "ALREADY EXISTS",
     "reason": "11 entries already in schedule_vaud.json. Wix site."},
    {"studio": "vivre-le-yoga.ch", "canton": "vaud", "status": "FOUND",
     "reason": "6 classes extracted from /cours/plan-des-cours-2/.", "classes": 6},
    {"studio": "yogacenter.ch", "canton": "vaud", "status": "NOT FOUND",
     "reason": "Schedule on /cours/ loads dynamically. Teachers: Patrick Nolfo, Ardiana Nolfo, etc."},
    {"studio": "caroledalmas.com", "canton": "vaud", "status": "FOUND",
     "reason": "3 classes extracted from yoga-de-l-energie page.", "classes": 3},

    # ZURICH (5 studios)
    {"studio": "soulcity-zurich.ch", "canton": "zurich", "status": "NOT FOUND",
     "reason": "Uses Bsport booking widget. Schedule loads dynamically."},
    {"studio": "studioy3.ch", "canton": "zurich", "status": "NOT FOUND",
     "reason": "Squarespace site with dynamic booking. Schedule not in HTML."},
    {"studio": "templeshape.com", "canton": "zurich", "status": "NOT FOUND",
     "reason": "Uses Bookee booking platform. Schedule loads dynamically."},
    {"studio": "projectpeace.ch", "canton": "zurich", "status": "FOUND",
     "reason": "1 class found (Jivamukti online, currently traveling).", "classes": 1},
    {"studio": "flowfabrik.ch", "canton": "zurich", "status": "NOT FOUND",
     "reason": "Wix site, all sub-pages 404. Schedule loads dynamically."},
]


# =============================================================================
# MAIN - Update schedule files
# =============================================================================

def main():
    print("=" * 70)
    print("CRACK MANUAL 45 - Adding verified schedule data for 45 studios")
    print(f"Date: {TODAY}")
    print("=" * 70)

    total_new_classes = 0
    total_studios_updated = 0

    # Group data by canton
    by_canton = {}
    for key, data in SCHEDULE_DATA.items():
        canton = data["canton"]
        if canton not in by_canton:
            by_canton[canton] = []
        by_canton[canton].append(data)

    for canton in sorted(by_canton.keys()):
        canton_data = by_canton[canton]
        sched_file = DATA_DIR / f"schedule_{canton}.json"

        print(f"\n--- CANTON: {canton.upper()} ---")

        # Load existing schedule
        if sched_file.exists():
            with open(sched_file) as f:
                sched = json.load(f)
        else:
            sched = {"last_updated": "", "classes": []}

        for studio_data in canton_data:
            sid = studio_data["studio_id"]
            name = studio_data["studio_name"]
            new_classes = studio_data["classes"]

            # Remove any existing unverified entries for this studio_id
            old_count = len(sched["classes"])
            sched["classes"] = [
                c for c in sched["classes"]
                if c.get("studio_id") != sid
            ]
            removed = old_count - len(sched["classes"])

            # Add new verified classes
            sched["classes"].extend(new_classes)
            total_new_classes += len(new_classes)
            total_studios_updated += 1

            print(f"  {name} ({sid}): +{len(new_classes)} classes"
                  f"{f' (replaced {removed} old)' if removed else ''}")

        # Update timestamp and save
        sched["last_updated"] = datetime.now(timezone.utc).isoformat()
        with open(sched_file, "w") as f:
            json.dump(sched, f, indent=2, ensure_ascii=False)
        print(f"  -> Saved {sched_file.name} ({len(sched['classes'])} total classes)")

    # Print full report
    print("\n" + "=" * 70)
    print("STUDIO INVESTIGATION REPORT")
    print("=" * 70)

    found = [r for r in STUDIO_REPORT if r["status"] == "FOUND"]
    not_found = [r for r in STUDIO_REPORT if r["status"] == "NOT FOUND"]
    already = [r for r in STUDIO_REPORT if r["status"] == "ALREADY EXISTS"]

    print(f"\nFOUND & ADDED: {len(found)} studios, {sum(r.get('classes', 0) for r in found)} classes")
    for r in found:
        print(f"  + {r['studio']:40s} [{r['canton']:15s}] {r['reason']}")

    print(f"\nALREADY IN DATABASE: {len(already)} studios")
    for r in already:
        print(f"  = {r['studio']:40s} [{r['canton']:15s}] {r['reason']}")

    print(f"\nNOT EXTRACTABLE: {len(not_found)} studios")
    for r in not_found:
        print(f"  x {r['studio']:40s} [{r['canton']:15s}] {r['reason']}")

    # Categorize failures
    print(f"\n{'=' * 70}")
    print("FAILURE ANALYSIS")
    print(f"{'=' * 70}")

    reasons = {}
    for r in not_found:
        reason_cat = "unknown"
        reason_text = r["reason"].lower()
        if "dynamically" in reason_text or "booking" in reason_text or "widget" in reason_text:
            reason_cat = "Dynamic booking platform (Bsport/Momence/Mindbody/Bookee/Healcode)"
        elif "wix" in reason_text and "404" in reason_text:
            reason_cat = "Wix site - schedule sub-pages return 404"
        elif "403" in reason_text or "blocks" in reason_text:
            reason_cat = "403 Forbidden - blocks automated access"
        elif "jpg" in reason_text or "image" in reason_text:
            reason_cat = "Schedule in image format (JPG), not machine-readable"
        elif "ssl" in reason_text or "certificate" in reason_text:
            reason_cat = "SSL certificate error"
        elif "private" in reason_text or "login" in reason_text:
            reason_cat = "Private/login-required site"
        elif "retreat" in reason_text or "no regular" in reason_text:
            reason_cat = "No regular weekly classes (retreats only)"
        elif "for sale" in reason_text:
            reason_cat = "Domain for sale - no active studio"
        elif "pause" in reason_text or "break" in reason_text:
            reason_cat = "Studio on break/pause"
        elif "national" in reason_text:
            reason_cat = "National platform - no direct schedule"
        if reason_cat not in reasons:
            reasons[reason_cat] = []
        reasons[reason_cat].append(r["studio"])

    for cat, studios in sorted(reasons.items(), key=lambda x: -len(x[1])):
        print(f"\n  {cat} ({len(studios)}):")
        for s in studios:
            print(f"    - {s}")

    print(f"\n{'=' * 70}")
    print(f"TOTALS: {total_studios_updated} studios updated, {total_new_classes} new classes added")
    print(f"Coverage: {len(found)} found + {len(already)} existing = {len(found)+len(already)} / 45 studios")
    print(f"Remaining: {len(not_found)} studios with no extractable data")
    print(f"{'=' * 70}")


if __name__ == "__main__":
    main()
