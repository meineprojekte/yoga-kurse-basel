#!/usr/bin/env python3
"""
Data Validation & Anomaly Detection System
===========================================
Run after each scrape (4x daily) to check all yoga studio data for anomalies.

Usage:
    python tools/validate_data.py

Generates:
    - tools/validation_report.json  (machine-readable)
    - tools/validation_report.txt   (human-readable)
    - tools/price_snapshot.json     (price history for change detection)
"""

import json
import os
import re
import math
from datetime import datetime
from pathlib import Path

# Paths
BASE_DIR = Path(__file__).resolve().parent.parent
DATA_DIR = BASE_DIR / "data"
TOOLS_DIR = BASE_DIR / "tools"
SNAPSHOT_FILE = TOOLS_DIR / "price_snapshot.json"
REPORT_JSON = TOOLS_DIR / "validation_report.json"
REPORT_TXT = TOOLS_DIR / "validation_report.txt"

# Price validation ranges (CHF)
PRICE_RANGES = {
    "single":  (10, 60),
    "card_10": (80, 500),
    "monthly": (50, 400),
    "trial":   (0, 80),
}

# Ratio checks
RATIO_CARD10_TO_SINGLE = (7, 12)   # 10er-Karte / single
RATIO_MONTHLY_TO_SINGLE = (4, 10)  # monthly / single

# Schedule validation
VALID_DAYS = {"Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday", "Sunday"}
MIN_CLASS_HOUR = 5   # 05:00
MAX_CLASS_HOUR = 23  # 23:00
MIN_DURATION_MIN = 30
MAX_DURATION_MIN = 180

# Switzerland coordinate bounds
CH_LAT = (45.8, 47.9)
CH_LNG = (5.9, 10.5)

# Canton ID to file suffix mapping
# Most cantons use their id directly, but basel-stadt uses "basel"
CANTON_FILE_MAP = {
    "basel-stadt": "basel",
}


def load_cantons():
    """Load canton definitions."""
    path = DATA_DIR / "cantons.json"
    if not path.exists():
        return []
    with open(path, "r", encoding="utf-8") as f:
        data = json.load(f)
    return data.get("cantons", [])


def canton_file_suffix(canton_id):
    """Map canton id to the file suffix used in studios_XXX.json / schedule_XXX.json."""
    return CANTON_FILE_MAP.get(canton_id, canton_id)


def load_all_studios():
    """Load studios from all canton files. Returns list of (canton_id, studio) tuples."""
    cantons = load_cantons()
    all_studios = []

    for canton in cantons:
        cid = canton["id"]
        suffix = canton_file_suffix(cid)
        path = DATA_DIR / f"studios_{suffix}.json"
        if not path.exists():
            continue
        try:
            with open(path, "r", encoding="utf-8") as f:
                data = json.load(f)
            for studio in data.get("studios", []):
                all_studios.append((cid, studio))
        except (json.JSONDecodeError, KeyError):
            pass

    return all_studios


def load_all_schedules():
    """Load schedules from all canton files. Returns list of (canton_id, class_entry) tuples."""
    cantons = load_cantons()
    all_classes = []

    for canton in cantons:
        cid = canton["id"]
        suffix = canton_file_suffix(cid)
        path = DATA_DIR / f"schedule_{suffix}.json"
        if not path.exists():
            continue
        try:
            with open(path, "r", encoding="utf-8") as f:
                data = json.load(f)
            for cls in data.get("classes", []):
                all_classes.append((cid, cls))
        except (json.JSONDecodeError, KeyError):
            pass

    return all_classes


def parse_time(t):
    """Parse HH:MM string to (hours, minutes) tuple. Returns None on failure."""
    if not t or not isinstance(t, str):
        return None
    m = re.match(r"^(\d{1,2}):(\d{2})$", t.strip())
    if not m:
        return None
    return int(m.group(1)), int(m.group(2))


def time_to_minutes(t):
    """Convert HH:MM to total minutes."""
    parsed = parse_time(t)
    if parsed is None:
        return None
    h, m = parsed
    return h * 60 + m


# ---------------------------------------------------------------------------
# Validation functions
# ---------------------------------------------------------------------------

def validate_prices(studios):
    """Check 1: Price range and ratio validation."""
    anomalies = []
    warnings = []

    for canton_id, studio in studios:
        pricing = studio.get("pricing")
        if not pricing:
            continue

        sid = studio.get("id", "unknown")
        sname = studio.get("name", "Unknown")
        source = pricing.get("source", "")

        single = pricing.get("single")
        card_10 = pricing.get("card_10")
        monthly = pricing.get("monthly")
        trial = pricing.get("trial")

        # Range checks
        for field, value in [("single", single), ("card_10", card_10),
                             ("monthly", monthly), ("trial", trial)]:
            if value is None:
                continue
            lo, hi = PRICE_RANGES[field]
            if not (lo <= value <= hi):
                anomalies.append({
                    "type": "price_out_of_range",
                    "severity": "high",
                    "studio_id": sid,
                    "studio_name": sname,
                    "canton": canton_id,
                    "field": f"pricing.{field}",
                    "value": value,
                    "expected_range": f"{lo}-{hi}",
                    "source": source,
                    "message": (
                        f"{field} CHF {value} ist ausserhalb des normalen "
                        f"Bereichs (CHF {lo}-{hi})"
                    ),
                })

        # Ratio: card_10 / single
        if single and card_10 and single > 0:
            ratio = card_10 / single
            lo, hi = RATIO_CARD10_TO_SINGLE
            if not (lo <= ratio <= hi):
                warnings.append({
                    "type": "price_ratio_unusual",
                    "severity": "medium",
                    "studio_id": sid,
                    "studio_name": sname,
                    "canton": canton_id,
                    "field": "pricing.card_10 / pricing.single",
                    "value": round(ratio, 2),
                    "expected_range": f"{lo}-{hi}x",
                    "source": source,
                    "message": (
                        f"10er-Karte/Einzeleintritt Verhältnis {ratio:.1f}x "
                        f"(erwartet {lo}-{hi}x)"
                    ),
                })

        # Ratio: monthly / single
        if single and monthly and single > 0:
            ratio = monthly / single
            lo, hi = RATIO_MONTHLY_TO_SINGLE
            if not (lo <= ratio <= hi):
                warnings.append({
                    "type": "price_ratio_unusual",
                    "severity": "medium",
                    "studio_id": sid,
                    "studio_name": sname,
                    "canton": canton_id,
                    "field": "pricing.monthly / pricing.single",
                    "value": round(ratio, 2),
                    "expected_range": f"{lo}-{hi}x",
                    "source": source,
                    "message": (
                        f"Monatsabo/Einzeleintritt Verhältnis {ratio:.1f}x "
                        f"(erwartet {lo}-{hi}x)"
                    ),
                })

        # Trial should be <= single
        if trial is not None and single is not None and trial > single:
            warnings.append({
                "type": "trial_exceeds_single",
                "severity": "medium",
                "studio_id": sid,
                "studio_name": sname,
                "canton": canton_id,
                "field": "pricing.trial vs pricing.single",
                "value": trial,
                "expected_range": f"<= {single}",
                "source": source,
                "message": (
                    f"Probepreis CHF {trial} ist höher als Einzeleintritt "
                    f"CHF {single}"
                ),
            })

    return anomalies, warnings


def detect_price_changes(studios):
    """Check 2: Compare current prices with saved snapshot."""
    price_changes = []

    # Build current price map
    current_prices = {}
    for canton_id, studio in studios:
        pricing = studio.get("pricing")
        if not pricing:
            continue
        sid = studio.get("id", "unknown")
        current_prices[sid] = {
            "name": studio.get("name", "Unknown"),
            "canton": canton_id,
            "source": pricing.get("source", ""),
            "prices": {
                k: pricing.get(k)
                for k in ("single", "card_10", "monthly", "trial")
                if pricing.get(k) is not None
            },
        }

    # Load previous snapshot
    first_run = False
    if SNAPSHOT_FILE.exists():
        try:
            with open(SNAPSHOT_FILE, "r", encoding="utf-8") as f:
                snapshot = json.load(f)
        except (json.JSONDecodeError, IOError):
            snapshot = {}
            first_run = True
    else:
        snapshot = {}
        first_run = True

    previous_prices = snapshot.get("studios", {})

    if not first_run:
        # Compare
        for sid, current in current_prices.items():
            prev = previous_prices.get(sid)
            if not prev:
                continue
            prev_p = prev.get("prices", {})
            for field, cur_val in current["prices"].items():
                old_val = prev_p.get(field)
                if old_val is None or cur_val is None or old_val == 0:
                    continue
                pct_change = abs(cur_val - old_val) / old_val * 100
                if pct_change > 20:
                    price_changes.append({
                        "type": "price_change",
                        "severity": "high" if pct_change > 50 else "medium",
                        "studio_id": sid,
                        "studio_name": current["name"],
                        "canton": current["canton"],
                        "field": f"pricing.{field}",
                        "old_value": old_val,
                        "new_value": cur_val,
                        "change_pct": round(pct_change, 1),
                        "source": current["source"],
                        "message": (
                            f"{field} geändert von CHF {old_val} auf "
                            f"CHF {cur_val} ({pct_change:+.0f}%)"
                        ),
                    })

    # Save current snapshot
    new_snapshot = {
        "timestamp": datetime.now().isoformat(),
        "studios": current_prices,
    }
    with open(SNAPSHOT_FILE, "w", encoding="utf-8") as f:
        json.dump(new_snapshot, f, indent=2, ensure_ascii=False)

    return price_changes, first_run


def validate_studios(studios):
    """Check 3: Studio data completeness and validity."""
    anomalies = []
    warnings = []

    for canton_id, studio in studios:
        sid = studio.get("id", "unknown")
        sname = studio.get("name", "")
        active = studio.get("active", True)

        if not active:
            continue

        # Name must not be empty
        if not sname or not sname.strip():
            anomalies.append({
                "type": "missing_name",
                "severity": "high",
                "studio_id": sid,
                "studio_name": "(leer)",
                "canton": canton_id,
                "field": "name",
                "value": sname,
                "message": "Studio hat keinen Namen",
            })

        # Must have at least one contact method
        website = studio.get("website", "")
        phone = studio.get("phone", "")
        email = studio.get("email", "")
        if not website and not phone and not email:
            warnings.append({
                "type": "no_contact_info",
                "severity": "medium",
                "studio_id": sid,
                "studio_name": sname,
                "canton": canton_id,
                "field": "website/phone/email",
                "value": "all empty",
                "message": "Kein Kontakt (Website, Telefon, E-Mail) vorhanden",
            })

        # Must have at least one address with city
        addresses = studio.get("addresses", [])
        has_city = any(a.get("city") for a in addresses)
        if not addresses or not has_city:
            warnings.append({
                "type": "missing_address",
                "severity": "medium",
                "studio_id": sid,
                "studio_name": sname,
                "canton": canton_id,
                "field": "addresses",
                "value": len(addresses),
                "message": "Keine Adresse mit Stadt vorhanden",
            })

        # Must have at least one yoga style
        styles = studio.get("styles", [])
        if not styles:
            warnings.append({
                "type": "no_styles",
                "severity": "low",
                "studio_id": sid,
                "studio_name": sname,
                "canton": canton_id,
                "field": "styles",
                "value": 0,
                "message": "Keine Yoga-Stile definiert",
            })

        # Coordinates within Switzerland
        lat = studio.get("lat")
        lng = studio.get("lng")
        if lat is not None and lng is not None:
            if not (CH_LAT[0] <= lat <= CH_LAT[1]) or not (CH_LNG[0] <= lng <= CH_LNG[1]):
                anomalies.append({
                    "type": "coordinates_outside_ch",
                    "severity": "high",
                    "studio_id": sid,
                    "studio_name": sname,
                    "canton": canton_id,
                    "field": "lat/lng",
                    "value": f"{lat}, {lng}",
                    "message": (
                        f"Koordinaten ({lat}, {lng}) liegen ausserhalb der "
                        f"Schweiz (lat {CH_LAT[0]}-{CH_LAT[1]}, "
                        f"lng {CH_LNG[0]}-{CH_LNG[1]})"
                    ),
                })

        # Website URL validation
        if website and not website.startswith("http"):
            warnings.append({
                "type": "invalid_url",
                "severity": "low",
                "studio_id": sid,
                "studio_name": sname,
                "canton": canton_id,
                "field": "website",
                "value": website,
                "message": f"Website URL beginnt nicht mit http: {website}",
            })

    return anomalies, warnings


def validate_schedule(classes, studio_ids):
    """Check 4: Schedule entry validation."""
    anomalies = []
    warnings = []
    orphan_counts = {}  # (studio_id, name, canton) -> count

    for canton_id, cls in classes:
        sid = cls.get("studio_id", "unknown")
        sname = cls.get("studio_name", "Unknown")
        day = cls.get("day", "")
        t_start = cls.get("time_start", "")
        t_end = cls.get("time_end", "")
        class_name = cls.get("class_name", "")

        label = f"{sname} - {class_name} ({day})"

        # Valid day
        if day not in VALID_DAYS:
            anomalies.append({
                "type": "invalid_day",
                "severity": "high",
                "studio_id": sid,
                "studio_name": sname,
                "canton": canton_id,
                "field": "day",
                "value": day,
                "message": f"Ungültiger Tag '{day}' für {label}",
            })

        # Parse times
        start_min = time_to_minutes(t_start)
        end_min = time_to_minutes(t_end)

        if start_min is None:
            warnings.append({
                "type": "invalid_time",
                "severity": "medium",
                "studio_id": sid,
                "studio_name": sname,
                "canton": canton_id,
                "field": "time_start",
                "value": t_start,
                "message": f"Ungültige Startzeit '{t_start}' für {label}",
            })
            continue

        if end_min is None:
            warnings.append({
                "type": "invalid_time",
                "severity": "medium",
                "studio_id": sid,
                "studio_name": sname,
                "canton": canton_id,
                "field": "time_end",
                "value": t_end,
                "message": f"Ungültige Endzeit '{t_end}' für {label}",
            })
            continue

        # Time range check
        start_h = start_min // 60
        if start_h < MIN_CLASS_HOUR or start_h >= MAX_CLASS_HOUR:
            warnings.append({
                "type": "unusual_class_time",
                "severity": "low",
                "studio_id": sid,
                "studio_name": sname,
                "canton": canton_id,
                "field": "time_start",
                "value": t_start,
                "message": (
                    f"Kurszeit {t_start} ausserhalb {MIN_CLASS_HOUR:02d}:00-"
                    f"{MAX_CLASS_HOUR:02d}:00 für {label}"
                ),
            })

        # End must be after start
        if end_min <= start_min:
            anomalies.append({
                "type": "end_before_start",
                "severity": "high",
                "studio_id": sid,
                "studio_name": sname,
                "canton": canton_id,
                "field": "time_end",
                "value": f"{t_start}-{t_end}",
                "message": f"Endzeit {t_end} liegt vor Startzeit {t_start} für {label}",
            })
            continue

        # Duration check
        duration = end_min - start_min
        if duration < MIN_DURATION_MIN or duration > MAX_DURATION_MIN:
            warnings.append({
                "type": "unusual_duration",
                "severity": "medium",
                "studio_id": sid,
                "studio_name": sname,
                "canton": canton_id,
                "field": "duration",
                "value": f"{duration} min",
                "message": (
                    f"Kursdauer {duration} Min. ausserhalb {MIN_DURATION_MIN}-"
                    f"{MAX_DURATION_MIN} Min. für {label}"
                ),
            })

        # Track orphan studio_ids for grouping (cross-reference, check 5)
        if sid not in studio_ids:
            orphan_key = (sid, sname, canton_id)
            orphan_counts[orphan_key] = orphan_counts.get(orphan_key, 0) + 1

    # Emit one anomaly per orphan studio_id (grouped)
    for (sid, sname, canton_id), count in orphan_counts.items():
        anomalies.append({
            "type": "orphan_schedule_entry",
            "severity": "high",
            "studio_id": sid,
            "studio_name": sname,
            "canton": canton_id,
            "field": "studio_id",
            "value": sid,
            "class_count": count,
            "message": (
                f"studio_id '{sid}' in Schedule existiert nicht in Studios-Daten "
                f"({count} Klassen betroffen)"
            ),
        })

    return anomalies, warnings


def detect_duplicates(studios):
    """Check 6: Duplicate studios by name, address, or coordinates."""
    warnings = []

    # Group by canton
    by_canton = {}
    for canton_id, studio in studios:
        by_canton.setdefault(canton_id, []).append(studio)

    for canton_id, canton_studios in by_canton.items():
        # Duplicate names in same canton
        names = {}
        for s in canton_studios:
            name = s.get("name", "").strip().lower()
            if not name:
                continue
            names.setdefault(name, []).append(s)

        for name, dupes in names.items():
            if len(dupes) > 1:
                ids = [d.get("id", "?") for d in dupes]
                warnings.append({
                    "type": "duplicate_name",
                    "severity": "medium",
                    "studio_id": ids[0],
                    "studio_name": dupes[0].get("name", ""),
                    "canton": canton_id,
                    "field": "name",
                    "value": ", ".join(ids),
                    "message": (
                        f"Gleicher Name '{dupes[0].get('name', '')}' bei "
                        f"{len(dupes)} Studios: {', '.join(ids)}"
                    ),
                })

        # Duplicate addresses in same canton
        addrs = {}
        for s in canton_studios:
            for a in s.get("addresses", []):
                key = (a.get("street", "").strip().lower(), a.get("zip", "").strip())
                if not key[0]:
                    continue
                addrs.setdefault(key, []).append(s)

        for key, dupes in addrs.items():
            if len(dupes) > 1:
                ids = list({d.get("id", "?") for d in dupes})
                if len(ids) > 1:
                    warnings.append({
                        "type": "duplicate_address",
                        "severity": "medium",
                        "studio_id": ids[0],
                        "studio_name": dupes[0].get("name", ""),
                        "canton": canton_id,
                        "field": "address",
                        "value": f"{key[0]}, {key[1]}",
                        "message": (
                            f"Gleiche Adresse '{key[0]}, {key[1]}' bei "
                            f"Studios: {', '.join(ids)}"
                        ),
                    })

        # Duplicate coordinates (within 0.001 degrees ~ 100m)
        coord_list = []
        for s in canton_studios:
            lat = s.get("lat")
            lng = s.get("lng")
            if lat is not None and lng is not None:
                coord_list.append((lat, lng, s))

        for i in range(len(coord_list)):
            for j in range(i + 1, len(coord_list)):
                lat1, lng1, s1 = coord_list[i]
                lat2, lng2, s2 = coord_list[j]
                if abs(lat1 - lat2) < 0.001 and abs(lng1 - lng2) < 0.001:
                    id1 = s1.get("id", "?")
                    id2 = s2.get("id", "?")
                    warnings.append({
                        "type": "duplicate_coordinates",
                        "severity": "low",
                        "studio_id": id1,
                        "studio_name": s1.get("name", ""),
                        "canton": canton_id,
                        "field": "lat/lng",
                        "value": f"({lat1},{lng1}) vs ({lat2},{lng2})",
                        "message": (
                            f"Sehr nahe Koordinaten: '{s1.get('name', '')}' "
                            f"und '{s2.get('name', '')}' (< 100m Abstand)"
                        ),
                    })

    return warnings


def generate_text_report(report):
    """Generate human-readable text report."""
    lines = []
    lines.append("=" * 70)
    lines.append("  YOGA KURSE SCHWEIZ - DATA VALIDATION REPORT")
    lines.append("=" * 70)
    lines.append(f"  Zeitpunkt: {report['timestamp']}")
    lines.append("")

    summary = report["summary"]
    lines.append("--- ZUSAMMENFASSUNG ---")
    lines.append(f"  Studios total:        {summary['total_studios']}")
    lines.append(f"  Studios aktiv:        {summary['total_active']}")
    lines.append(f"  Studios mit Preisen:  {summary['total_with_pricing']}")
    lines.append(f"  Klassen total:        {summary['total_classes']}")
    lines.append(f"  Kantone geladen:      {summary['cantons_loaded']}")
    lines.append("")
    lines.append(f"  ANOMALIEN (hoch):     {summary['anomalies_found']}")
    lines.append(f"  WARNUNGEN (mittel+):  {summary['warnings_found']}")
    lines.append(f"  PREISÄNDERUNGEN:      {summary['price_changes_found']}")

    if summary.get("first_run"):
        lines.append("")
        lines.append("  [INFO] Erster Lauf - Preis-Snapshot erstellt.")
        lines.append("         Preisänderungen werden ab dem nächsten Lauf erkannt.")

    if report["anomalies"]:
        lines.append("")
        lines.append("=" * 70)
        lines.append("  ANOMALIEN (erfordern Aufmerksamkeit)")
        lines.append("=" * 70)
        for i, a in enumerate(report["anomalies"], 1):
            lines.append(f"")
            lines.append(f"  [{i}] {a['type']} | Schweregrad: {a['severity']}")
            lines.append(f"      Studio: {a['studio_name']} ({a['studio_id']})")
            lines.append(f"      Kanton: {a['canton']}")
            lines.append(f"      {a['message']}")
            if a.get("source"):
                lines.append(f"      Quelle: {a['source']}")

    if report["warnings"]:
        lines.append("")
        lines.append("=" * 70)
        lines.append("  WARNUNGEN (zur Überprüfung)")
        lines.append("=" * 70)
        for i, w in enumerate(report["warnings"], 1):
            lines.append(f"")
            lines.append(f"  [{i}] {w['type']} | Schweregrad: {w['severity']}")
            lines.append(f"      Studio: {w['studio_name']} ({w['studio_id']})")
            lines.append(f"      Kanton: {w['canton']}")
            lines.append(f"      {w['message']}")

    if report["price_changes"]:
        lines.append("")
        lines.append("=" * 70)
        lines.append("  PREISÄNDERUNGEN (> 20%)")
        lines.append("=" * 70)
        for i, pc in enumerate(report["price_changes"], 1):
            lines.append(f"")
            lines.append(f"  [{i}] {pc['studio_name']} ({pc['canton']})")
            lines.append(f"      {pc['field']}: CHF {pc['old_value']} -> CHF {pc['new_value']} ({pc['change_pct']:+.0f}%)")
            if pc.get("source"):
                lines.append(f"      Quelle: {pc['source']}")

    if not report["anomalies"] and not report["warnings"] and not report["price_changes"]:
        lines.append("")
        lines.append("  Alles in Ordnung! Keine Anomalien oder Warnungen gefunden.")

    lines.append("")
    lines.append("=" * 70)
    lines.append(f"  Report generiert: {report['timestamp']}")
    lines.append("=" * 70)
    lines.append("")

    return "\n".join(lines)


def main():
    print("Lade Daten...")

    # Load all data
    all_studios = load_all_studios()
    all_classes = load_all_schedules()

    # Build set of known studio IDs
    studio_ids = {s.get("id") for _, s in all_studios if s.get("id")}

    # Count cantons loaded
    cantons_loaded = len({canton_id for canton_id, _ in all_studios})

    total_studios = len(all_studios)
    total_active = sum(1 for _, s in all_studios if s.get("active", True))
    total_with_pricing = sum(1 for _, s in all_studios if s.get("pricing"))
    total_classes = len(all_classes)

    print(f"  {total_studios} Studios aus {cantons_loaded} Kantonen geladen")
    print(f"  {total_classes} Stundenplan-Einträge geladen")
    print()

    all_anomalies = []
    all_warnings = []

    # 1. Price validation
    print("Prüfe Preise...")
    price_anomalies, price_warnings = validate_prices(all_studios)
    all_anomalies.extend(price_anomalies)
    all_warnings.extend(price_warnings)
    print(f"  {len(price_anomalies)} Anomalien, {len(price_warnings)} Warnungen")

    # 2. Price change detection
    print("Prüfe Preisänderungen...")
    price_changes, first_run = detect_price_changes(all_studios)
    if first_run:
        print("  Erster Lauf - Snapshot erstellt")
    else:
        print(f"  {len(price_changes)} Preisänderungen erkannt")

    # 3. Studio data validation
    print("Prüfe Studio-Daten...")
    studio_anomalies, studio_warnings = validate_studios(all_studios)
    all_anomalies.extend(studio_anomalies)
    all_warnings.extend(studio_warnings)
    print(f"  {len(studio_anomalies)} Anomalien, {len(studio_warnings)} Warnungen")

    # 4 + 5. Schedule validation (includes cross-reference)
    print("Prüfe Stundenplan...")
    schedule_anomalies, schedule_warnings = validate_schedule(all_classes, studio_ids)
    all_anomalies.extend(schedule_anomalies)
    all_warnings.extend(schedule_warnings)
    print(f"  {len(schedule_anomalies)} Anomalien, {len(schedule_warnings)} Warnungen")

    # 6. Duplicate detection
    print("Prüfe Duplikate...")
    dup_warnings = detect_duplicates(all_studios)
    all_warnings.extend(dup_warnings)
    print(f"  {len(dup_warnings)} mögliche Duplikate")

    # Build report
    report = {
        "timestamp": datetime.now().isoformat(),
        "summary": {
            "total_studios": total_studios,
            "total_active": total_active,
            "total_with_pricing": total_with_pricing,
            "total_classes": total_classes,
            "cantons_loaded": cantons_loaded,
            "anomalies_found": len(all_anomalies),
            "warnings_found": len(all_warnings),
            "price_changes_found": len(price_changes),
            "first_run": first_run,
        },
        "anomalies": all_anomalies,
        "warnings": all_warnings,
        "price_changes": price_changes,
    }

    # Write JSON report
    with open(REPORT_JSON, "w", encoding="utf-8") as f:
        json.dump(report, f, indent=2, ensure_ascii=False)
    print(f"\nJSON-Report: {REPORT_JSON}")

    # Write text report
    text = generate_text_report(report)
    with open(REPORT_TXT, "w", encoding="utf-8") as f:
        f.write(text)
    print(f"Text-Report: {REPORT_TXT}")

    # Print summary
    print()
    print(f"Ergebnis: {len(all_anomalies)} Anomalien, "
          f"{len(all_warnings)} Warnungen, "
          f"{len(price_changes)} Preisänderungen")

    if all_anomalies:
        print("\n⚠ ANOMALIEN gefunden - bitte prüfen!")

    return report


if __name__ == "__main__":
    main()
