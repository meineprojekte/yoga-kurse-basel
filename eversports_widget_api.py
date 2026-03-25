#!/usr/bin/env python3
"""
Eversports Widget GraphQL API Client
=====================================
Reverse-engineered from the Eversports widget JavaScript bundle.

ENDPOINT: https://graphql-widget-master.production.eversports.cloud/api/graphql
AUTH: None required (CORS: access-control-allow-origin: *)

Widget IDs: UUID format (e.g., "9b862b1f-0890-4cd4-a438-34ca83062213")
  - Each studio creates widgets in their Eversports Manager dashboard
  - Each widget gets a UUID that is used as the data-eversports-widget-id in HTML
  - Widget IDs are NOT the same as the old /widget/w/SHORTCODE URLs

HOW TO FIND WIDGET IDs:
  1. Visit a studio website that uses the NEW Eversports widget
  2. Look in the HTML source for: <div data-eversports-widget-id="UUID-HERE"></div>
  3. Or intercept network traffic to graphql-widget-master.production.eversports.cloud

AVAILABLE WIDGET TYPES:
  - WidgetActivitySchedule (class schedule with times, teachers, etc.)
  - WidgetPrices (pricing/membership info)
  - WidgetActivityGroups (courses, workshops, retreats)
  - WidgetVideos (on-demand videos)
  - WidgetVouchers (gift vouchers)
  - WidgetNewsletter (newsletter signup)
"""

import json
import urllib.request
from datetime import datetime, timedelta

GRAPHQL_ENDPOINT = "https://graphql-widget-master.production.eversports.cloud/api/graphql"

# ============================================================================
# GraphQL Queries (extracted from widget JS bundle)
# ============================================================================

LOADER_WIDGET_QUERY = """
query LoaderWidget($widgetId: ID!) {
  widget(id: $widgetId) {
    __typename
    ... on WidgetActivitySchedule {
      id
      marketplaceURL
      settings {
        colorFontCard
        colorBackground
        colorButton
        colorFont
        fontFamily
        groupSchedule
        showLevel
        showResource
        showTrainer
        spotLimitDisplayType
        showCompactViewMobile
        isMyBookingsLinkVisible
        isVenueFilterHidden
        isTeacherFilterHidden
        isActivityGroupFilterHidden
        isSportFilterHidden
      }
      company { id }
      venues { nodes { id name } }
    }
    ... on WidgetPrices {
      id
      marketplaceURL
      invoicingVenue { id }
      company { id }
    }
    ... on WidgetActivityGroups {
      id
      marketplaceURL
      company { id }
      venues { nodes { id name } }
    }
    ... on WidgetVouchers {
      id
      marketplaceURL
      company { id }
    }
  }
}
"""

ACTIVITY_SCHEDULE_QUERY = """
query ActivityScheduleWidget(
  $widgetId: ID!
  $timeRange: TimeRangeInput
  $types: [ActivityGroupType!]
  $activityGroupIds: [ID!]
  $sportIds: [ID!]
  $teacherIds: [ID!]
  $first: Int
  $after: Cursor
) {
  widget(id: $widgetId) {
    __typename
    ... on WidgetActivitySchedule {
      id
      activities(
        activityGroupTypes: $types
        activityGroupPublicationStates: [ACTIVE, VIEW_ONLY]
        timeRange: $timeRange
        first: $first
        after: $after
        activityGroupIds: $activityGroupIds
        sportIds: $sportIds
        teacherIds: $teacherIds
        isArchived: false
      ) {
        nodes {
          id
          name
          start
          end
          activityGroup {
            id
            category { id name }
            color
            detailsPageURL
            name
            level
            limited { freeSpots totalSpots }
            sport { id name }
            venue { id name }
          }
          detailsPageURL
          hasOnlineStream
          isCancelled
          limited { freeSpots totalSpots }
          room { id name }
          teacher {
            id
            name
            imageV2 { url(size: X_SMALL) }
          }
        }
        pageInfo {
          hasNextPage
          endCursor
        }
      }
    }
  }
}
"""

FILTERS_QUERY = """
query FiltersWidget($widgetId: ID!) {
  widget(id: $widgetId) {
    __typename
    ... on WidgetActivitySchedule {
      id
      sportFilterOptions { nodes { isSelected value { id name } } }
      teacherFilterOptions { nodes { isSelected value { id name } } }
      venues { nodes { id name } }
    }
  }
}
"""


def graphql_request(query, variables=None, operation_name=None):
    """Make a GraphQL request to the Eversports widget API."""
    payload = {"query": query}
    if variables:
        payload["variables"] = variables
    if operation_name:
        payload["operationName"] = operation_name

    data = json.dumps(payload).encode("utf-8")
    req = urllib.request.Request(
        GRAPHQL_ENDPOINT,
        data=data,
        headers={"Content-Type": "application/json", "Accept": "application/json"},
    )

    with urllib.request.urlopen(req) as resp:
        return json.loads(resp.read().decode("utf-8"))


def get_widget_info(widget_id):
    """Get basic widget information and type."""
    return graphql_request(LOADER_WIDGET_QUERY, {"widgetId": widget_id}, "LoaderWidget")


def get_schedule(widget_id, days_ahead=7, first=100):
    """Get activity schedule for a widget."""
    now = datetime.utcnow()
    end = now + timedelta(days=days_ahead)

    variables = {
        "widgetId": widget_id,
        "timeRange": {
            "start": now.strftime("%Y-%m-%dT00:00:00.000Z"),
            "end": end.strftime("%Y-%m-%dT23:59:59.999Z"),
        },
        "first": first,
    }

    return graphql_request(
        ACTIVITY_SCHEDULE_QUERY, variables, "ActivityScheduleWidget"
    )


def get_filters(widget_id):
    """Get available filter options (sports, teachers, venues) for a widget."""
    return graphql_request(FILTERS_QUERY, {"widgetId": widget_id}, "FiltersWidget")


# ============================================================================
# Demo / Test
# ============================================================================

if __name__ == "__main__":
    # Test with a known working widget ID (voucher type)
    test_id = "9b862b1f-0890-4cd4-a438-34ca83062213"
    print(f"Testing widget API with ID: {test_id}")
    result = get_widget_info(test_id)
    print(json.dumps(result, indent=2))

    # To test with a SCHEDULE widget, you need to find a valid schedule widget UUID
    # by visiting a studio website that uses the new Eversports widget embed
    # (look for <div data-eversports-widget-id="..."> in their HTML source)
    #
    # Example usage once you have a schedule widget ID:
    # schedule = get_schedule("your-schedule-widget-uuid-here", days_ahead=7)
    # for activity in schedule['data']['widget']['activities']['nodes']:
    #     print(f"{activity['start']} - {activity['name']} with {activity['teacher']['name']}")

    print("\n" + "=" * 60)
    print("GraphQL API Schema (introspection):")
    schema = graphql_request('{ __schema { queryType { fields { name } } } }')
    print(json.dumps(schema, indent=2))
