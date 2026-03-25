# API Endpoints for Wix, Squarespace, and MindBody Yoga Studio Websites

## Test Date: 2026-03-22 (Updated: 2026-03-22 — Calendar V3 Discovery)

---

## 1. WIX BOOKINGS API

### Working Endpoints

#### Endpoint A: Services Catalog
**`POST {website}/_api/bookings/v2/services/query`**

Returns the service catalog (class names, prices, capacity, durations, locations).

#### Endpoint B: Calendar Events (WEEKLY SCHEDULE) — NEW DISCOVERY
**`POST {website}/_api/calendar/v3/events/query`**

**This is the breakthrough endpoint.** Returns actual calendar events with:
- Class name (title)
- Exact day + time (start.localDate, end.localDate)
- Timezone (Europe/Zurich)
- Recurrence rules (frequency: WEEKLY, days: ['MONDAY'], interval: 1)
- Capacity and remaining spots
- Status (CONFIRMED)

### Authentication Flow (2 steps)

**Step 1: Get instance token**
```
GET {website}/_api/v2/dynamicmodel
```
Returns JSON with an `apps` object. The Wix Bookings app ID is `13d21c63-b5ec-5912-8397-c3a5ddb27a97`. Extract its `instance` value.

**Step 2a: Query services (catalog)**
```
POST {website}/_api/bookings/v2/services/query
Headers:
  Content-Type: application/json
  Authorization: {instance_token}
Body: {"query":{"filter":{"type":"CLASS"}}}
```

**Step 2b: Query calendar events (WEEKLY SCHEDULE)**
```
POST {website}/_api/calendar/v3/events/query
Headers:
  Content-Type: application/json
  Authorization: {instance_token}
Body: {"query":{"filter":{},"paging":{"limit":100}}}
```

This returns actual class instances with recurrence rules. Each event contains:
- `title`: Class name (e.g., "Vinyasa Yoga")
- `start.localDate`: Start datetime (e.g., "2026-03-23T18:45:00")
- `end.localDate`: End datetime
- `start.timeZone`: Timezone (e.g., "Europe/Zurich")
- `recurrenceType`: "INSTANCE" for recurring classes
- `recurrenceRule.frequency`: "WEEKLY"
- `recurrenceRule.days`: ["MONDAY"] — the day(s) of the week
- `recurrenceRule.interval`: 1 (every week)
- `totalCapacity`, `remainingCapacity`
- `status`: "CONFIRMED"
- `type`: "CLASS"

### How to Detect Wix Sites
Look for these markers in page source:
- `static.parastorage.com` or `static.wixstatic.com` in script/CSS sources
- `"brand":"wix"` in viewer model config
- `window.thunderboltVersion` in JavaScript

### How to Check if Site Has Wix Bookings
After getting `_api/v2/dynamicmodel`, check if app ID `13d21c63-b5ec-5912-8397-c3a5ddb27a97` exists in the `apps` object. If not present, the site does not use Wix Bookings.

### Data Returned

Each service object contains:
```json
{
  "id": "uuid",
  "type": "CLASS|COURSE|APPOINTMENT",
  "name": "Vinyasa Yoga",
  "tagLine": "Flow Fiesta Programm",
  "defaultCapacity": 15,
  "hidden": false,
  "category": {
    "name": "Weekly Classes"
  },
  "payment": {
    "rateType": "FIXED",
    "fixed": {
      "price": {"value": "30", "currency": "CHF"}
    }
  },
  "locations": [{
    "calculatedAddress": {
      "formattedAddress": "Postgasse 37, Bern, Schweiz",
      "city": "Bern",
      "postalCode": "3011",
      "geocode": {"latitude": 46.9487338, "longitude": 7.4542257}
    },
    "business": {
      "name": "YAMA Yoga & Co",
      "email": "yoga@yamabern.ch",
      "phone": "+41763921327"
    }
  }],
  "schedule": {
    "firstSessionStart": "2023-08-02T15:30:00Z",
    "lastSessionEnd": "2026-10-29T17:45:00Z",
    "availabilityConstraints": {
      "sessionDurations": [75]
    }
  },
  "onlineBooking": {"enabled": true},
  "urls": {
    "servicePage": {"url": "https://www.yamabern.ch/service-page/vinyasa-yoga"},
    "bookingPage": {"url": "https://www.yamabern.ch/booking-calendar/vinyasa-yoga"}
  },
  "bookingPolicy": {
    "cancellationPolicy": {...},
    "waitlistPolicy": {"enabled": true, "capacity": 10}
  }
}
```

### What You Get vs What You Don't

**Available:**
- Class/service names and descriptions
- Service type (CLASS, COURSE, APPOINTMENT)
- Category (e.g., "Weekly Classes")
- Price (single class) and currency
- Full address with geocode
- Business name, email, phone
- Capacity
- Session duration (minutes)
- Date range (firstSessionStart, lastSessionEnd)
- Booking page URLs
- Cancellation/waitlist policies

**NOT available via the Services API alone:**
- ~~Recurring day-of-week schedule~~ **NOW AVAILABLE via Calendar V3 Events API!**
- Teacher/instructor names (partially available in `resources` field of events)
- ~~Actual session instances/calendar~~ **NOW AVAILABLE!**

### SOLVED: Weekly Recurring Schedule via Calendar V3
The Calendar V3 Events API (`/_api/calendar/v3/events/query`) returns the complete weekly schedule with recurrence rules. This was previously documented as impossible.

**Verified on yamabern.ch** — returned 50 events with complete weekly timetable:
- Monday: Hatha Flow 12:30, Gentle Hatha Flow 17:30, Vinyasaflow 19:15
- Tuesday: Morning Bliss 07:00, Synergy Vinyasa Yoga 09:00 & 10:30, Lunchflow 12:15, Hatha Flow 17:45, Vinyasaflow 19:15, Candle light Yoga 21:00
- Wednesday: Surfyoga 12:15, Basicflow 17:30, Evening Flow 19:30
- Thursday: Morning Flow 09:00, Lunchflow for Beginner 12:15, Kundalini Yoga 19:15
- Friday: Lunchflow 12:15, Spirit Power-Flow 17:30
- Saturday: What the Core?! 10:00

### Studios Tested
| Studio | URL | Services | Calendar Events | Notes |
|--------|-----|----------|-----------------|-------|
| YAMA Yoga & Co | yamabern.ch | 61 (36 CLASS) | 50 events, full weekly timetable | Both APIs work perfectly |
| FlowFabrik | flowfabrik.ch | 6 (3 CLASS) | 50 events (2018 data) | Calendar API works, old data |

### Endpoints That FAILED
| Endpoint | Status | Notes |
|----------|--------|-------|
| `_api/bookings-viewer/visitor/services/list` | 406/404 | Old API, deprecated |
| `_api/bookings/v1/catalog/services` | 404 | Old API |
| `_api/bookings/v2/sessions/list` | 404 | Not accessible |
| `_api/bookings/v2/sessions/query` | 404 | Not accessible |
| `_api/bookings/v2/availability/query` | 404 | Not accessible |
| `_api/wix-bookings-availability-api/api/public/availability/query` | 403 | Forbidden |
| `_api/wix-one-events-server/v1/events/query` | 404 | Not on these sites |
| `_api/bookings/v1/calendar/sessions/query` | 404 | Not accessible |
| `_api/wix-bookings/v2/sessions/query` | 403 | Needs different auth |
| `_api/bookings/v1/calendar/schedules` | 404 | Not accessible |
| `_serverless/bookings-viewer-server/*` | 404 | Not on these sites |

### Endpoints That WORK
| Endpoint | Method | Auth | Returns |
|----------|--------|------|---------|
| `_api/v2/dynamicmodel` | GET | None | Instance tokens for all apps |
| `_api/bookings/v2/services/query` | POST | Instance token | Service catalog (names, prices, capacity) |
| `_api/calendar/v3/events/query` | POST | Instance token | **Weekly schedule with day/time/recurrence** |

---

## 2. SQUARESPACE API

### Working Endpoint

**`GET {website}/events?format=json`**

Append `?format=json` to any Squarespace page URL to get its data as JSON.

### How to Detect Squarespace Sites
Look for these markers:
- `assets.squarespace.com` in script/CSS sources
- `Static.SQUARESPACE_CONTEXT` in page source
- `SQUARESPACE_ROLLUPS` in JavaScript
- `.squarespace.com` subdomain references
- CSS classes starting with `sqs-`

### What Works

**Events pages**: `{website}/events?format=json`
Returns event data in `upcoming` and `past` arrays at the top level of the response.

**Any page**: `{website}/{slug}?format=json`
Returns the page structure with `mainContent` (HTML of the page body), which can contain embedded iframe URLs to booking platforms.

### Events Data Structure
```json
{
  "upcoming": [
    {
      "title": "50 Hours Naad Yoga Training",
      "startDate": 1780106400000,
      "endDate": 1782712800000,
      "location": {
        "addressTitle": "Jio Kundalini Yoga",
        "addressLine1": "25 Kernstrasse",
        "addressLine2": "Zurich, ZH, 8004"
      },
      "fullUrl": "/events/50-hours-naad-yoga-training",
      "urlId": "50-hours-naad-yoga-training",
      "excerpt": "...",
      "tags": [],
      "categories": []
    }
  ],
  "past": [...]
}
```

**Key fields:** `title`, `startDate` (Unix ms), `endDate` (Unix ms), `location`, `fullUrl`, `excerpt`

### What Squarespace Events Are Good For
- **Workshop/retreat listings**: One-off events with specific dates
- **Teacher trainings**: Multi-day events
- **Special events**: Cacao ceremonies, retreats, etc.

### What Squarespace Events Are NOT Good For
- **Weekly class schedules**: Studios typically don't put recurring yoga classes in Squarespace Events. Instead they use external booking platforms (Eversports, MindBody, etc.) embedded via iframes.

### Extracting Embedded Booking Widgets
Use `{website}/{slug}?format=json` and parse the `mainContent` HTML for iframe src URLs:
```python
import re
iframes = re.findall(r'src=["\']?(https?://[^"\'>\s]+)', main_content)
# Example: "https://widget.eversports.com/w/he9wvj"
```

### Studios Tested
| Studio | URL | Events Found | Notes |
|--------|-----|-------------|-------|
| Jio Kundalini Yoga | jiokundaliniyoga.com | 5 upcoming, 1 past | Workshops & trainings, classes via Eversports widget |
| Studio Y3 | studioy3.ch | 0 | Empty /book page, uses dynamic blocks |
| Soul City | soulcity-zurich.ch | 0 | Empty /classes page, uses dynamic blocks |

### Endpoints That FAILED
| Pattern | Status | Notes |
|---------|--------|-------|
| `{website}/schedule?format=json` | 404 | Only works if a page with slug "schedule" exists |
| `{website}/classes?format=json` | 200 but empty | Page exists but content loads dynamically |

---

## 3. IMPLEMENTATION RECOMMENDATIONS

### For the Scraper

#### Wix Sites with Bookings — COMPLETE SOLUTION
```python
import requests
from datetime import datetime

def scrape_wix_bookings(website_url):
    """Scrape class catalog + weekly schedule from Wix Bookings sites."""
    # Step 1: Get auth token
    dynamic = requests.get(f"{website_url}/_api/v2/dynamicmodel").json()

    BOOKINGS_APP_ID = "13d21c63-b5ec-5912-8397-c3a5ddb27a97"
    if BOOKINGS_APP_ID not in dynamic.get("apps", {}):
        return None  # No Wix Bookings on this site

    instance = dynamic["apps"][BOOKINGS_APP_ID]["instance"]
    headers = {
        "Content-Type": "application/json",
        "Authorization": instance
    }

    # Step 2: Query services (catalog with prices, capacity, etc.)
    svc_resp = requests.post(
        f"{website_url}/_api/bookings/v2/services/query",
        headers=headers,
        json={"query": {"filter": {"type": "CLASS"}}}
    )
    services = svc_resp.json().get("services", [])

    # Step 3: Query calendar events (weekly schedule with day/time)
    events_resp = requests.post(
        f"{website_url}/_api/calendar/v3/events/query",
        headers=headers,
        json={"query": {"filter": {}, "paging": {"limit": 100}}}
    )
    events = events_resp.json().get("events", [])

    # Build weekly schedule from events
    weekly_schedule = {}  # key: "ClassName-DAY-HH:MM" to dedupe
    for event in events:
        if event.get("type") != "CLASS" or event.get("status") != "CONFIRMED":
            continue

        title = event.get("title", "")
        start = event.get("start", {}).get("localDate", "")
        end = event.get("end", {}).get("localDate", "")
        rrule = event.get("recurrenceRule", {})

        if not start:
            continue

        dt = datetime.fromisoformat(start)
        time_str = dt.strftime("%H:%M")

        # Get day of week from recurrence rule (most reliable)
        days = rrule.get("days", []) if isinstance(rrule, dict) else []
        if not days:
            # Fallback: derive from date
            days = [dt.strftime("%A").upper()]

        for day in days:
            key = f"{title}-{day}-{time_str}"
            if key not in weekly_schedule:
                end_dt = datetime.fromisoformat(end) if end else None
                duration = int((end_dt - dt).total_seconds() / 60) if end_dt else None
                weekly_schedule[key] = {
                    "name": title,
                    "day": day,
                    "time": time_str,
                    "end_time": end_dt.strftime("%H:%M") if end_dt else None,
                    "duration_minutes": duration,
                    "capacity": event.get("totalCapacity"),
                    "schedule_id": event.get("scheduleId"),
                }

    # Enrich with price data from services
    svc_by_schedule = {}
    for svc in services:
        if not svc.get("hidden"):
            sid = svc.get("schedule", {}).get("id", "")
            svc_by_schedule[sid] = svc

    classes = list(weekly_schedule.values())
    for cls in classes:
        svc = svc_by_schedule.get(cls.get("schedule_id"), {})
        if svc:
            price_info = svc.get("payment", {}).get("fixed", {}).get("price", {})
            cls["price"] = price_info.get("value", "")
            cls["currency"] = price_info.get("currency", "")
            locations = svc.get("locations", [])
            if locations:
                cls["address"] = locations[0].get("calculatedAddress", {}).get("formattedAddress", "")
            cls["booking_url"] = svc.get("urls", {}).get("bookingPage", {}).get("url", "")

    return classes
```

#### Squarespace Sites
```python
import requests
import re
from datetime import datetime

def scrape_squarespace_events(website_url):
    """Scrape events from Squarespace sites."""
    response = requests.get(f"{website_url}/events?format=json")
    if response.status_code != 200:
        return None

    data = response.json()
    upcoming = data.get("upcoming", [])

    events = []
    for event in upcoming:
        start = event.get("startDate")
        end = event.get("endDate")
        loc = event.get("location", {})

        events.append({
            "title": event.get("title", ""),
            "start": datetime.fromtimestamp(start / 1000).isoformat() if start else None,
            "end": datetime.fromtimestamp(end / 1000).isoformat() if end else None,
            "location": f"{loc.get('addressTitle', '')} {loc.get('addressLine1', '')} {loc.get('addressLine2', '')}".strip(),
            "url": f"{website_url}{event.get('fullUrl', '')}",
        })

    return events

def find_embedded_booking_widget(website_url, page_slug):
    """Find embedded booking platform widgets in Squarespace pages."""
    response = requests.get(f"{website_url}/{page_slug}?format=json")
    if response.status_code != 200:
        return None

    main_content = response.json().get("mainContent", "")
    iframes = re.findall(r'src=["\']?(https?://[^"\'>\s]+)', main_content)

    # Filter for known booking platforms
    booking_urls = [u for u in iframes if any(p in u for p in [
        "eversports", "mindbody", "teamup", "momoyoga", "bsport", "acuity"
    ])]

    return booking_urls
```

### Platform Detection Helper
```python
def detect_platform(website_url):
    """Detect if a website is built on Wix or Squarespace."""
    response = requests.get(website_url, timeout=10)
    html = response.text.lower()

    if "parastorage.com" in html or "wixstatic.com" in html or "thunderboltversion" in html:
        return "wix"
    elif "squarespace.com" in html or "squarespace_context" in html or "sqs-block" in html:
        return "squarespace"
    else:
        return "unknown"
```

---

## 3. MINDBODY API

### Overview
MindBody-powered studios (e.g., B.Yoga Basel) use MindBody's scheduling platform. There are multiple API tiers available.

### How to Detect MindBody Studios
Look for these markers in page source:
- `mindbody.io` or `mindbodyonline.com` in URLs
- `<healcode-widget>` HTML elements
- `widgets.mindbodyonline.com/javascripts/healcode.js` script
- `video.mindbody.io/studios/{id}` video URLs (reveals Studio ID)
- `data-mb-site-id` attributes in widget embed codes

### Known Studio IDs
| Studio | Studio ID | Source |
|--------|-----------|--------|
| B.Yoga Basel | 6743 | video.mindbody.io URL on byoga.ch |

### API Tier 1: MindBody Affiliate API (RECOMMENDED)
**Base URL:** `https://mb-api.mindbodyonline.com/affiliate/api/v1`

**Authentication:** API key + Basic Auth (client key:secret encoded in Base64)
```
Headers:
  API-Key: {your_api_key}
  Authorization: Basic {base64(clientKey:clientSecret)}
  User-Agent: YogaKurseBasel/1.0
```

**To get credentials:** Sign up at https://developers.mindbodyonline.com/ as a developer.

**Key Endpoints:**
| Endpoint | Method | Description |
|----------|--------|-------------|
| `/locations` | GET | Search studios by lat/lon, radius, keyword |
| `/locations/{id}/classes` | GET | **Get class schedule for a specific studio** |
| `/locations/{id}/pricingoptions` | GET | Get pricing for a location |
| `/classes/{id}/pricingoptions` | GET | Get pricing for specific classes |

**Location Search Parameters:**
- `latitude`, `longitude`: Geographic center
- `radius`: Search radius
- `searchText`: Category or business name filter
- `maxResults`, `offset`: Pagination

### API Tier 2: MindBody Public API V6
**Base URL:** `https://api.mindbodyonline.com/public/v6`

**Authentication:** API-Key header + optional SiteId header + optional user token
```
Headers:
  Api-Key: {your_api_key}
  SiteId: {studio_id}
```

**Key Endpoints:**
| Endpoint | Method | Description |
|----------|--------|-------------|
| `/class/classes` | GET | Get classes (needs API key, returns limited data without token) |
| `/class/classschedules` | GET | Get class schedules |
| `/site/sites` | GET | Get site/studio info |

**Note:** Without a user token, some data is limited (hidden classes not returned, etc.).

### API Tier 3: Branded Web Widgets (Healcode)
Studios embed schedule widgets using `<healcode-widget>` elements. These widgets:
- Load via `https://widgets.mindbodyonline.com/javascripts/healcode.js`
- Use `data-site-id` (Branded Web ID) and `data-mb-site-id` (MindBody Studio ID)
- Render class schedules dynamically via JavaScript
- Have a `/print` endpoint at `https://widgets.healcode.com/widgets/schedules/{widget_id}/print`

**Print endpoint status:** Returns schedule HTML when widget is properly configured. Many return "Widget not found" errors. Requires JavaScript rendering for full data.

### API Tier 4: MindBody Explore Gateway
**Base URL:** `https://prod-mkt-gateway.mindbody.io/v1`

This is the API powering MindBody's consumer search at mindbodyonline.com/explore. Returns Elasticsearch results.

**Tested Endpoints:**
| Endpoint | Status | Notes |
|----------|--------|-------|
| `/search/locations?filter.latitude=...&filter.longitude=...&filter.radius=...` | 200 | Returns 0 results for Basel (maybe not indexed in Switzerland) |

### MindBody Implementation Recommendation
```python
import requests
import base64

def scrape_mindbody_classes(studio_id, api_key, client_key, client_secret):
    """Scrape class schedule from MindBody Affiliate API."""
    credentials = base64.b64encode(f"{client_key}:{client_secret}".encode()).decode()

    headers = {
        "API-Key": api_key,
        "Authorization": f"Basic {credentials}",
        "User-Agent": "YogaKurseBasel/1.0"
    }

    # Get classes for this studio
    response = requests.get(
        f"https://mb-api.mindbodyonline.com/affiliate/api/v1/locations/{studio_id}/classes",
        headers=headers
    )

    if response.status_code == 200:
        return response.json()
    return None
```

### Endpoints That FAILED
| Endpoint | Status | Notes |
|----------|--------|-------|
| `clients.mindbodyonline.com/classic/ws?studioid=...` | 403 | Cloudflare protection |
| `widgets.healcode.com/widgets/schedules/{id}` | "Widget not found" | Widget ID may be expired |
| `brandedweb.mindbodyonline.com/widget/schedule/{id}` | 404 | Not a valid endpoint |
| `go.mindbody.io/book/widgets/schedules/view/{id}/schedule` | ECONNREFUSED | Server not accessible |
| `prod-mkt-gateway.mindbody.io/v1/studios/{id}/classes` | 404 | Wrong endpoint path |
| `prod-mkt-gateway.mindbody.io/v1/search/classes?...` | 403 | Requires auth |

---

## 4. SUMMARY

| Platform | Endpoint | Auth Required | Data Quality | Best For |
|----------|----------|---------------|--------------|----------|
| **Wix** | `_api/bookings/v2/services/query` | Yes (instance token) | High: names, prices, capacity, durations | Class catalog |
| **Wix** | `_api/calendar/v3/events/query` | Yes (instance token) | **Excellent: day, time, recurrence, capacity** | **Weekly timetable** |
| **MindBody** | Affiliate API `/locations/{id}/classes` | Yes (API key + Basic Auth) | High: full class schedule | Weekly timetable |
| **Squarespace** | `/events?format=json` | No | Medium: events with dates | Workshops, retreats |
| **Squarespace** | `/{page}?format=json` | No | Low: HTML with iframe URLs | Finding booking widgets |

### Key Findings
1. **Wix recurring schedules ARE available** via Calendar V3 Events API - SOLVED
2. **MindBody class schedules** available via Affiliate API (requires free developer signup)
3. **Squarespace events are workshops, not classes**: Weekly schedules managed by external platforms
4. **No headless browser needed for Wix!** Pure REST API calls work

### Remaining Challenges
1. **MindBody API requires developer credentials**: Free signup at developers.mindbodyonline.com
2. **MindBody Cloudflare protection**: Direct client portal scraping blocked
3. **Some studios may not use Wix Bookings or MindBody**: Those still need manual entry or headless scraping
