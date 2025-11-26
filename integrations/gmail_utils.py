import base64
import email
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
import requests
from django.utils import timezone
from datetime import timedelta
from django.conf import settings
from users.models import OrganizationConfigurations


def refresh_google_token(integration):
    """Refresh Google access token using refresh token."""
    org_config = OrganizationConfigurations.objects.filter(organization=integration.org).first()
    if not org_config or not org_config.google_client_id or not org_config.google_client_secret:
        raise RuntimeError("Google OAuth is not configured")
    
    token_url = "https://oauth2.googleapis.com/token"
    data = {
        "client_id": org_config.google_client_id,
        "client_secret": org_config.google_client_secret,
        "refresh_token": integration.refresh_token,
        "grant_type": "refresh_token",
    }
    
    resp = requests.post(token_url, data=data, timeout=15)
    resp.raise_for_status()
    token_data = resp.json()
    
    access_token = token_data.get("access_token")
    expires_in = token_data.get("expires_in", 3600)
    expires_at = timezone.now() + timedelta(seconds=expires_in)
    
    integration.access_token = access_token
    integration.expires_at = expires_at
    integration.save(update_fields=["access_token", "expires_at"])
    
    return access_token


def get_valid_access_token(integration):
    """Get a valid access token, refreshing if necessary."""
    if integration.expires_at and timezone.now() >= integration.expires_at - timedelta(minutes=5):
        return refresh_google_token(integration)
    return integration.access_token


def send_gmail_email(integration, to_email, subject, body, from_email=None):
    """Send an email via Gmail API."""
    access_token = get_valid_access_token(integration)
    
    # Create message
    message = MIMEMultipart()
    message['to'] = to_email
    message['subject'] = subject
    if from_email:
        message['from'] = from_email
    
    message.attach(MIMEText(body, 'plain'))
    
    # Encode message
    raw_message = base64.urlsafe_b64encode(message.as_bytes()).decode('utf-8')
    
    # Send via Gmail API
    url = "https://gmail.googleapis.com/gmail/v1/users/me/messages/send"
    headers = {
        "Authorization": f"Bearer {access_token}",
        "Content-Type": "application/json",
    }
    data = {"raw": raw_message}
    
    resp = requests.post(url, json=data, headers=headers, timeout=15)
    resp.raise_for_status()
    return resp.json()


def fetch_gmail_messages(integration, query="", max_results=50):
    """Fetch Gmail messages."""
    access_token = get_valid_access_token(integration)
    
    # First, get message list
    url = "https://gmail.googleapis.com/gmail/v1/users/me/messages"
    headers = {"Authorization": f"Bearer {access_token}"}
    params = {"maxResults": max_results}
    if query:
        params["q"] = query
    
    resp = requests.get(url, headers=headers, params=params, timeout=15)
    resp.raise_for_status()
    messages_list = resp.json()
    
    messages = []
    for msg in messages_list.get("messages", [])[:max_results]:
        # Get full message details
        msg_url = f"https://gmail.googleapis.com/gmail/v1/users/me/messages/{msg['id']}"
        msg_resp = requests.get(msg_url, headers=headers, params={"format": "full"}, timeout=15)
        msg_resp.raise_for_status()
        msg_data = msg_resp.json()
        
        # Parse headers
        headers_dict = {h["name"]: h["value"] for h in msg_data.get("payload", {}).get("headers", [])}
        
        # Extract body
        body = ""
        payload = msg_data.get("payload", {})
        if "parts" in payload:
            for part in payload["parts"]:
                if part.get("mimeType") == "text/plain":
                    body = base64.urlsafe_b64decode(part["body"]["data"]).decode("utf-8", errors="ignore")
                    break
        elif payload.get("body", {}).get("data"):
            body = base64.urlsafe_b64decode(payload["body"]["data"]).decode("utf-8", errors="ignore")
        
        messages.append({
            "id": msg_data["id"],
            "thread_id": msg_data.get("threadId"),
            "subject": headers_dict.get("Subject", ""),
            "from": headers_dict.get("From", ""),
            "to": headers_dict.get("To", ""),
            "date": headers_dict.get("Date", ""),
            "body": body,
            "snippet": msg_data.get("snippet", ""),
        })
    
    return messages


def fetch_gmail_replies(integration, thread_id):
    """Fetch replies for a specific thread."""
    access_token = get_valid_access_token(integration)
    
    url = f"https://gmail.googleapis.com/gmail/v1/users/me/threads/{thread_id}"
    headers = {"Authorization": f"Bearer {access_token}"}
    
    resp = requests.get(url, headers=headers, params={"format": "full"}, timeout=15)
    resp.raise_for_status()
    thread_data = resp.json()
    
    replies = []
    for msg in thread_data.get("messages", []):
        headers_dict = {h["name"]: h["value"] for h in msg.get("payload", {}).get("headers", [])}
        
        body = ""
        payload = msg.get("payload", {})
        if "parts" in payload:
            for part in payload["parts"]:
                if part.get("mimeType") == "text/plain":
                    body = base64.urlsafe_b64decode(part["body"]["data"]).decode("utf-8", errors="ignore")
                    break
        elif payload.get("body", {}).get("data"):
            body = base64.urlsafe_b64decode(payload["body"]["data"]).decode("utf-8", errors="ignore")
        
        replies.append({
            "id": msg["id"],
            "from": headers_dict.get("From", ""),
            "to": headers_dict.get("To", ""),
            "subject": headers_dict.get("Subject", ""),
            "date": headers_dict.get("Date", ""),
            "body": body,
            "snippet": msg.get("snippet", ""),
        })
    
    return replies

