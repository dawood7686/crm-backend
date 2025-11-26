from celery import shared_task


@shared_task(bind=True, max_retries=3, default_retry_delay=60)
def sync_calls_task(self, org_id):
    """
    Sync recent HubSpot calls for an org.
    """
    from .models import Integration
    from .utils import hubspot_api_request
    from activities.models import ActivityTimeline
    try:
        integration = Integration.objects.get(org_id=org_id, provider="hubspot")
    except Integration.DoesNotExist:
        return {"error": "no hubspot integration"}

    # HubSpot v3 calls endpoint
    path = "/crm/v3/objects/calls"
    params = {"limit": 100, "properties": ["hs_call_body", "hs_call_duration", "hs_call_title", "hs_call_direction"]}
    data = hubspot_api_request(integration, "GET", path, params=params)

    results = data.get("results", [])
    synced = 0
    for c in results:
        call_id = c["id"]
        props = c["properties"]

        activity, created = ActivityTimeline.objects.update_or_create(
            org=integration.org,
            external_id=f"hubspot:{call_id}",
            defaults={
                "type": "call",
                "title": props.get("hs_call_title") or "HubSpot Call",
                "description": props.get("hs_call_body") or "",
                "duration": int(props.get("hs_call_duration") or 0),
                "direction": props.get("hs_call_direction") or "UNKNOWN",
                "source": "hubspot",
            },
        )
        synced += 1
    return {"synced": synced}
