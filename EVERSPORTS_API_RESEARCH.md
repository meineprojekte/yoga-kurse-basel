# Eversports Schedule Data: Reverse Engineering Research

## WORKING APPROACH: Widget GraphQL API

### Endpoint
```
POST https://graphql-widget-master.production.eversports.cloud/api/graphql
Content-Type: application/json
```

### Authentication
**NONE REQUIRED** - The API has `access-control-allow-origin: *` and accepts unauthenticated requests.

### How It Works
1. Studios create widgets in Eversports Manager (Settings > Widgets)
2. Each widget gets a UUID (e.g., `9b862b1f-0890-4cd4-a438-34ca83062213`)
3. Studios embed on their website: `<div data-eversports-widget-id="UUID"></div>`
4. The widget JS at `widget-static.eversports.io/loader.js` calls this GraphQL API
5. Schedule data flows: Eversports Manager → GraphQL API → Widget → User's browser

### Widget Types
- `WidgetActivitySchedule` - Class schedules (the one we need!)
- `WidgetPrices` - Pricing info
- `WidgetActivityGroups` - Courses, workshops, retreats
- `WidgetVideos` - On-demand videos
- `WidgetVouchers` - Gift vouchers
- `WidgetNewsletter` - Newsletter signup

### Key GraphQL Queries (extracted from JS bundle)

#### 1. LoaderWidget - Get widget type and config
```graphql
query LoaderWidget($widgetId: ID!) {
  widget(id: $widgetId) {
    __typename
    ... on WidgetActivitySchedule {
      id
      marketplaceURL
      company { id }
      venues { nodes { id name } }
    }
  }
}
```

#### 2. ActivityScheduleWidget - Get actual schedule data
```graphql
query ActivityScheduleWidget($widgetId: ID!, $timeRange: TimeRangeInput, $first: Int, $after: Cursor) {
  widget(id: $widgetId) {
    ... on WidgetActivitySchedule {
      activities(
        activityGroupPublicationStates: [ACTIVE, VIEW_ONLY]
        timeRange: $timeRange
        first: $first
        after: $after
        isArchived: false
      ) {
        nodes {
          id, name, start, end
          activityGroup { name, level, sport { name }, venue { name } }
          teacher { name }
          isCancelled
          limited { freeSpots totalSpots }
          room { name }
        }
        pageInfo { hasNextPage endCursor }
      }
    }
  }
}
```

### Confirmed Working
- API endpoint responds to queries (tested and confirmed)
- Introspection works (full schema available)
- Widget queries return data with valid widget IDs
- Tested with voucher widget ID: `9b862b1f-0890-4cd4-a438-34ca83062213`

### The Widget ID Challenge
- Old widget URLs like `/widget/w/3kuhpu` use SHORT CODES → do NOT work with new API
- New widget system uses UUID-format widget IDs
- Studios must create "new-style" widgets in Eversports Manager
- To find a studio's schedule widget ID: inspect their website HTML for `data-eversports-widget-id`
- The new widget system is relatively recent (announced ~2024), so adoption may still be growing

---

## OTHER APIs INVESTIGATED

### Aggregator API
- **Endpoint:** `https://aggregator.eversports.io/v1/graphql`
- **Auth:** Bearer token required (403 on data queries)
- **Schema:** Open for introspection (sessions, venues, reservations, sports)
- **Intended for:** Third-party aggregators (ClassPass, Wellhub, etc.)
- **Access:** Contact support@eversports.com

### Provider API
- **Endpoint:** `https://provider-api.eversportsmanager.io/api/graphql`
- **Auth:** Credentials required (403 on data queries)
- **Schema:** Open for introspection (activities, venues, teachers, companies)
- **Access:** Contact support@eversports.com for API credentials

### Old REST API (defunct)
- **Endpoint:** `https://api.eversport.at/v2/` (connection refused)
- **Format:** JSON:API
- **Status:** No longer accessible

### Eversports.ch Direct Access
- **Blocked by:** Cloudflare challenge page (403)
- **Even with:** Browser User-Agent, Googlebot UA, headless Chrome
- **Conclusion:** Not viable for scraping

---

## Source Files
- `eversports_widget_api.py` - Python client for the Widget GraphQL API
- JS source analyzed: `widget-static.eversports.io/loader.js` and chunks
- API URL found in: `chunk-WOXNNFUM.js` (the graphql-request client module)

## Next Steps
1. Find studios with new-style widget embeds (data-eversports-widget-id)
2. Or: Contact Eversports for Provider API access (official route)
3. Or: Create an Eversports Manager account to generate widget IDs for test studios
