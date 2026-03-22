# API Endpoints for Wix and Squarespace Yoga Studio Websites

## Test Date: 2026-03-22

---

## 1. WIX BOOKINGS API

### Working Endpoint

**`POST {website}/_api/bookings/v2/services/query`**

This is the only Wix API endpoint that works reliably for extracting class/service data.

### Authentication Flow (2 steps)

**Step 1: Get instance token**
```
GET {website}/_api/v2/dynamicmodel
```
Returns JSON with an `apps` object. The Wix Bookings app ID is `13d21c63-b5ec-5912-8397-c3a5ddb27a97`. Extract its `instance` value.

**Step 2: Query services**
```
POST {website}/_api/bookings/v2/services/query
Headers:
  Content-Type: application/json
  Authorization: {instance_token}
Body: {"query":{"filter":{"type":"CLASS"}}}
```

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

**NOT available via this API:**
- Recurring day-of-week schedule (e.g., "Mondays at 18:00")
- Teacher/instructor names
- Actual session instances/calendar
- The sessions/availability/calendar endpoints all return 404 or 403

### Limitation: No Recurring Schedule
The API does NOT return the weekly recurring schedule (which day/time each class runs). This data is loaded dynamically by the Wix Bookings calendar widget on the client side. The `firstSessionStart` timestamp can hint at the day/time pattern but is unreliable for recurring schedules.

### Studios Tested
| Studio | URL | Services Found | Notes |
|--------|-----|----------------|-------|
| YAMA Yoga & Co | yamabern.ch | 61 (36 CLASS) | Rich data, all fields populated |
| FlowFabrik | flowfabrik.ch | 6 (3 CLASS) | Old schedule dates (2018-2019), site may not actively use Wix Bookings |

### Endpoints That FAILED
| Endpoint | Status | Notes |
|----------|--------|-------|
| `_api/bookings-viewer/visitor/services/list` | 406/404 | Old API, deprecated |
| `_api/bookings/v1/catalog/services` | 404 | Old API |
| `_api/bookings/v2/sessions/list` | 404 | Not accessible |
| `_api/bookings/v2/availability/query` | 404 | Not accessible |
| `_api/wix-bookings-availability-api/api/public/availability/query` | 403 | Forbidden |
| `_api/wix-one-events-server/v1/events/query` | 404 | Not on these sites |
| `_api/bookings/v2/sessions/query` | 404 | Not accessible |

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

#### Wix Sites with Bookings
```python
import requests

def scrape_wix_bookings(website_url):
    """Scrape class data from Wix Bookings sites."""
    # Step 1: Get auth token
    dynamic = requests.get(f"{website_url}/_api/v2/dynamicmodel").json()

    BOOKINGS_APP_ID = "13d21c63-b5ec-5912-8397-c3a5ddb27a97"
    if BOOKINGS_APP_ID not in dynamic.get("apps", {}):
        return None  # No Wix Bookings on this site

    instance = dynamic["apps"][BOOKINGS_APP_ID]["instance"]

    # Step 2: Query services
    response = requests.post(
        f"{website_url}/_api/bookings/v2/services/query",
        headers={
            "Content-Type": "application/json",
            "Authorization": instance
        },
        json={"query": {"filter": {"type": "CLASS"}}}
    )

    services = response.json().get("services", [])

    classes = []
    for svc in services:
        if svc.get("hidden"):
            continue

        schedule = svc.get("schedule", {})
        durations = schedule.get("availabilityConstraints", {}).get("sessionDurations", [])
        price_info = svc.get("payment", {}).get("fixed", {}).get("price", {})
        locations = svc.get("locations", [])
        address = ""
        if locations:
            address = locations[0].get("calculatedAddress", {}).get("formattedAddress", "")

        classes.append({
            "name": svc["name"],
            "description": svc.get("tagLine", ""),
            "type": svc["type"],
            "category": svc.get("category", {}).get("name", ""),
            "price": price_info.get("value", ""),
            "currency": price_info.get("currency", ""),
            "capacity": svc.get("defaultCapacity", 0),
            "duration_minutes": durations[0] if durations else None,
            "address": address,
            "booking_url": svc.get("urls", {}).get("bookingPage", {}).get("url", ""),
            "first_session": schedule.get("firstSessionStart", ""),
            "last_session": schedule.get("lastSessionEnd", ""),
        })

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

## 4. SUMMARY

| Platform | Endpoint | Auth Required | Data Quality | Best For |
|----------|----------|---------------|--------------|----------|
| **Wix** | `_api/bookings/v2/services/query` | Yes (instance token from `_api/v2/dynamicmodel`) | High: names, prices, addresses, capacity, durations | Class catalog (names, prices, locations) |
| **Squarespace** | `/events?format=json` | No | Medium: events with dates, locations | Workshops, retreats, special events |
| **Squarespace** | `/{page}?format=json` | No | Low: HTML content with possible iframe URLs | Finding embedded booking widgets |

### Key Limitations
1. **No recurring schedules from Wix**: Cannot get "Mondays at 18:00" - only service definitions
2. **Squarespace events are workshops, not classes**: Weekly yoga class schedules are managed by external platforms (Eversports, MindBody, etc.)
3. **Both platforms load schedule data dynamically**: A headless browser (Playwright/Puppeteer) would be needed to capture the actual rendered schedule with day/time slots
