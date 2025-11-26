# apps/integrations/utils.py
import requests
from django.utils import timezone
from datetime import timedelta
from django.conf import settings
from .models import Integration
from users.models import OrganizationConfigurations

HUBSPOT_TOKEN_URL = "https://api.hubapi.com/oauth/v1/token"
HUBSPOT_API_BASE = "https://api.hubapi.com"

def refresh_hubspot_token(integration: Integration):
    if not integration.refresh_token:
        raise RuntimeError("No refresh token available")
    
    org_config = OrganizationConfigurations.objects.filter(organization=integration.org).first()
    if not org_config or not org_config.hubspot_client_id or not org_config.hubspot_client_secret:
        raise RuntimeError("HubSpot OAuth is not configured")

    data = {
        "grant_type": "refresh_token",
        "client_id": org_config.hubspot_client_id,
        "client_secret": org_config.hubspot_client_secret,
        "refresh_token": integration.refresh_token,
    }
    headers = {"Content-Type": "application/x-www-form-urlencoded"}
    resp = requests.post(HUBSPOT_TOKEN_URL, data=data, headers=headers, timeout=15)
    resp.raise_for_status()
    token_data = resp.json()
    expires_in = token_data.get("expires_in")
    expires_at = timezone.now() + timedelta(seconds=int(expires_in)) if expires_in else None
    integration.access_token = token_data["access_token"]
    if token_data.get("refresh_token"):
        integration.refresh_token = token_data["refresh_token"]
    integration.expires_at = expires_at
    integration.save(update_fields=["access_token", "refresh_token", "expires_at"])
    return integration.access_token

def hubspot_api_request(integration: Integration, method: str, path: str, **kwargs):
    """
    Generic helper. Tries request and refreshes token on 401
    `path` is the API path, e.g. "/crm/v3/objects/contacts"
    """
    access = integration.access_token
    headers = kwargs.pop("headers", {})
    headers.setdefault("Authorization", f"Bearer {access}")
    url = HUBSPOT_API_BASE + path
    resp = requests.request(method, url, headers=headers, timeout=20, **kwargs)
    if resp.status_code == 401:
        # try refresh
        access = refresh_hubspot_token(integration)
        headers["Authorization"] = f"Bearer {access}"
        resp = requests.request(method, url, headers=headers, timeout=20, **kwargs)
    resp.raise_for_status()
    return resp.json()
