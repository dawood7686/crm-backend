import datetime
import urllib

import jwt
from django.http import JsonResponse
from rest_framework import status
from rest_framework.permissions import IsAuthenticated

from users.models import Organization, User, OrganizationConfigurations
from .models import Integration
from django.utils import timezone
import requests
from rest_framework.views import APIView
from rest_framework.response import Response
from django.conf import settings
from urllib.parse import urlencode
from django.shortcuts import redirect

class GoogleOAuthInitView(APIView):
    """
    Initiates Google OAuth by redirecting user to Google's consent page.
    Frontend calls this endpoint and is redirected to Google OAuth.
    """
    permission_classes = [IsAuthenticated]
    def get(self, request):
        state_payload = {"user_id": str(request.user.id)}
        organization_config = OrganizationConfigurations.objects.filter(organization=request.user.org).last()
        if not organization_config or not organization_config.google_client_id or not organization_config.google_client_secret:
            return Response({"error": "Google OAuth is not configured for this organization."}, status=status.HTTP_400_BAD_REQUEST)
        state_token = jwt.encode(state_payload, settings.SECRET_KEY, algorithm="HS256")

        # Redirect URI (callback endpoint)
        redirect_uri = f"{request.scheme}://{request.get_host()}/api/v1/integrations/google/callback/"
        # OAuth scopes
        scopes = [
            "openid",
            "email",
            "profile",
            "https://www.googleapis.com/auth/gmail.readonly",
            "https://www.googleapis.com/auth/gmail.send",
            "https://www.googleapis.com/auth/gmail.modify"
        ]
        base_url = "https://accounts.google.com/o/oauth2/v2/auth"
        params = {
            "client_id": organization_config.google_client_id,
            "redirect_uri": redirect_uri,
            "response_type": "code",
            "scope": " ".join(scopes),
            "access_type": "offline",  # ensures refresh token
            "prompt": "consent",  # always show consent screen
            "state": state_token,
        }

        auth_url = f"{base_url}?{urlencode(params)}"
        return Response({"auth_url": auth_url})


class GmailOAuthCallbackView(APIView):
    """
    Receives code from frontend, exchanges for tokens, stores in Integration.
    """
    def get(self, request):
        try:
            code = request.query_params.get("code")
            state = request.query_params.get("state")
            
            if not state:
                return JsonResponse({"error": "Missing 'state' parameter"}, status=400)
            
            if not code:
                return JsonResponse({"error": "Missing 'code' parameter"}, status=400)
            
            try:
                payload = jwt.decode(state.encode(), settings.SECRET_KEY, algorithms=["HS256"])
            except jwt.InvalidTokenError as e:
                return JsonResponse({"error": f"Invalid state token: {str(e)}"}, status=400)
            
            user_id = payload.get("user_id")
            if not user_id:
                return JsonResponse({"error": "Invalid state token: missing user_id"}, status=400)
            
            try:
                user = User.objects.get(id=user_id)
            except User.DoesNotExist:
                return JsonResponse({"error": "User not found"}, status=404)
            
            organization_config = OrganizationConfigurations.objects.filter(organization=user.org).last()
            if not organization_config or not organization_config.google_client_id or not organization_config.google_client_secret:
                return JsonResponse({"error": "Google OAuth is not configured for this organization."}, status=400)

            redirect_uri = f"{request.scheme}://{request.get_host()}/api/v1/integrations/google/callback/"

            token_url = "https://oauth2.googleapis.com/token"
            data = {
                "code": code,
                "client_id": organization_config.google_client_id,
                "client_secret": organization_config.google_client_secret,
                "redirect_uri": redirect_uri,
                "grant_type": "authorization_code",
            }

            # Exchange code for tokens
            try:
                r = requests.post(token_url, data=data, timeout=10)
                r.raise_for_status()
                token_data = r.json()
            except requests.RequestException as e:
                return JsonResponse({"error": f"Failed to exchange token: {str(e)}"}, status=500)
            
            access_token = token_data.get("access_token")
            refresh_token = token_data.get("refresh_token")
            expires_in = token_data.get("expires_in", 3600)

            if not access_token:
                error_msg = token_data.get("error_description", token_data.get("error", "Unknown error"))
                return JsonResponse({"error": f"Failed to get access token: {error_msg}", "details": token_data}, status=400)

            # Save or update integration
            try:
                integration, created = Integration.objects.update_or_create(
                    org=user.org,
                    provider="gmail",
                    defaults={
                        "access_token": access_token,
                        "refresh_token": refresh_token,
                        "expires_at": timezone.now() + timezone.timedelta(seconds=expires_in),
                    }
                )
            except Exception as e:
                return JsonResponse({"error": f"Failed to save integration: {str(e)}"}, status=500)

            # Get frontend URL from settings or use default
            frontend_origins = getattr(settings, 'FRONTEND_ORIGINS', 'http://localhost:3000')
            frontend_url = frontend_origins.split(',')[0].strip() if frontend_origins else 'http://localhost:3000'
            
            # Return HTML page that closes popup and notifies parent window
            # Escape braces for f-string
            post_message_data = '{"type": "GOOGLE_OAUTH_SUCCESS", "provider": "gmail"}'
            html_content = f"""<!DOCTYPE html>
<html>
<head>
    <title>Google OAuth Success</title>
</head>
<body>
    <script>
        // Close the popup window
        try {{
            window.opener.postMessage({post_message_data}, '{frontend_url}');
        }} catch (e) {{
            console.error('Failed to post message:', e);
        }}
        setTimeout(function() {{
            window.close();
        }}, 100);
    </script>
    <p>Authorization successful! This window will close automatically.</p>
</body>
</html>"""
            from django.http import HttpResponse
            return HttpResponse(html_content, content_type='text/html')
            
        except Exception as e:
            import traceback
            error_trace = traceback.format_exc()
            return JsonResponse({
                "error": "Internal server error",
                "message": str(e),
                "trace": error_trace if settings.DEBUG else None
            }, status=500)

# class HubSpotOAuthCallbackView(APIView):
#     """
#     Exchange code for HubSpot tokens.
#     """
#     permission_classes = [IsAuthenticated]
#
#     def post(self, request):
#         code = request.data.get("code")
#         redirect_uri = request.data.get("redirect_uri")
#         token_url = "https://api.hubapi.com/oauth/v1/token"
#         data = {
#             "grant_type": "authorization_code",
#             "client_id": "HUBSPOT_CLIENT_ID",
#             "client_secret": "HUBSPOT_CLIENT_SECRET",
#             "redirect_uri": redirect_uri,
#             "code": code
#         }
#         r = requests.post(token_url, data=data)
#         token_data = r.json()
#         Integration.objects.update_or_create(
#             org=request.user.org,
#             provider="hubspot",
#             defaults={
#                 "access_token": token_data["access_token"],
#                 "refresh_token": token_data.get("refresh_token"),
#                 "expires_at": timezone.now() + timezone.timedelta(seconds=token_data["expires_in"]),
#             }
#         )
#         return JsonResponse({"status": "ok"}, status=status.HTTP_200_OK)
#
class HubspotOAuthInitView(APIView):
    """Redirects user to HubSpot OAuth consent screen."""
    permission_classes = [IsAuthenticated]

    def get(self, request):
        org_config = OrganizationConfigurations.objects.filter(
            organization=request.user.org
        ).last()
        if not org_config or not org_config.hubspot_client_id or not org_config.hubspot_client_secret:
            return Response({"error": "HubSpot OAuth is not configured for this organization."}, status=status.HTTP_400_BAD_REQUEST)

        state = jwt.encode(
            {"user_id": str(request.user.id), "ts": datetime.datetime.utcnow().timestamp()},
            settings.SECRET_KEY,
            algorithm="HS256",
        )
        scopes = [
            "crm.objects.contacts.read",
            "crm.objects.contacts.write",
            "crm.schemas.contacts.read",
            "crm.schemas.contacts.write",
            "oauth"
        ]
        scope_str = " ".join(scopes)

        # redirect_uri = f"{request.scheme}://localhost:8000/api/v1/integrations/hubspot/callback/"
        # auth_url = (
        #     "https://app-na2.hubspot.com/oauth/authorize"
        #     f"?client_id={org_config.hubspot_client_id}"
        #     f"&redirect_uri={redirect_uri}"
        #     f"&scope=contacts%20oauth"
        #     f"&state={scope_str}"
        # )
        redirect_uri = "http://localhost:8000/api/v1/integrations/hubspot/callback/"

        params = {
            "client_id": org_config.hubspot_client_id,
            "redirect_uri": redirect_uri,
            "scope": scope_str,
            "state": state
        }
        auth_url = f"https://app-na2.hubspot.com/oauth/authorize?{urllib.parse.urlencode(params)}"

        return Response({"auth_url": auth_url})


class HubspotOAuthCallbackView(APIView):
    """Handles HubSpot callback and stores tokens."""
    def get(self, request):
        code = request.query_params.get("code")
        state = request.query_params.get("state")

        try:
            payload = jwt.decode(state, settings.SECRET_KEY, algorithms=["HS256"])
            user_id = payload.get("user_id")
        except Exception as e:
            return JsonResponse({"error": "Invalid state", "details": str(e)}, status=400)

        user = User.objects.get(id=user_id)
        org_config = OrganizationConfigurations.objects.filter(
            organization=user.org
        ).last()
        if not org_config or not org_config.hubspot_client_id or not org_config.hubspot_client_secret:
            return Response({"error": "HubSpot OAuth is not configured for this organization."}, status=status.HTTP_400_BAD_REQUEST)

        redirect_uri = f"{request.scheme}://{request.get_host()}/api/v1/integrations/hubspot/callback/"

        token_url = "https://api.hubapi.com/oauth/v1/token"
        data = {
            "grant_type": "authorization_code",
            "client_id": org_config.hubspot_client_id,
            "client_secret": org_config.hubspot_client_secret,
            "redirect_uri": redirect_uri,
            "code": code,
        }

        r = requests.post(token_url, data=data, headers={"Content-Type": "application/x-www-form-urlencoded"})
        token_data = r.json()

        if "access_token" not in token_data:
            return JsonResponse({"error": "Failed to fetch tokens", "details": token_data}, status=400)

        expires_in = token_data.get("expires_in")  # e.g., 21600 seconds
        expires_at = timezone.now() + datetime.timedelta(seconds=expires_in) if expires_in else None

        Integration.objects.update_or_create(
            org=user.org,
            provider="hubspot",
            defaults={
                "access_token": token_data["access_token"],
                "refresh_token": token_data.get("refresh_token"),
                "expires_at": expires_at,  # ✅ proper datetime
            },
        )

        return JsonResponse({
            "message": "HubSpot connected successfully",
            "tokens": token_data
        })

class HubspotSyncContactsView(APIView):
    """Fetch contacts from HubSpot."""
    permission_classes = [IsAuthenticated]

    def get(self, request):
        org = getattr(request.user, "org", None)
        if not org:
            return Response({"error": "User not linked to any organization"}, status=400)

        try:
            integration = Integration.objects.get(org=org, provider="hubspot")
        except Integration.DoesNotExist:
            return Response({"error": "HubSpot not connected"}, status=400)

        url = "https://api.hubapi.com/crm/v3/objects/contacts"
        headers = {"Authorization": f"Bearer {integration.access_token}"}

        r = requests.get(url, headers=headers)
        if r.status_code != 200:
            return Response({"error": "Failed to fetch contacts", "details": r.json()}, status=400)

        contacts = r.json().get("results", [])

        # (Optional) You can save contacts into your Lead model here
        return Response({"contacts": contacts})


class IntegrationStatusView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        org = getattr(request.user, "org", None)
        if not org:
            return Response({"integrations": []})

        integrations = Integration.objects.filter(org=org)
        data = []
        for integration in integrations:
            data.append(
                {
                    "id": str(integration.id),
                    "provider": integration.provider,
                    "expires_at": integration.expires_at,
                }
            )
        return Response({"integrations": data})


class IntegrationDisconnectView(APIView):
    permission_classes = [IsAuthenticated]

    def delete(self, request, provider):
        provider = provider.lower()
        valid_providers = [choice[0] for choice in Integration.PROVIDER_CHOICES]
        if provider not in valid_providers:
            return Response({"error": "Unsupported provider"}, status=status.HTTP_400_BAD_REQUEST)

        org = getattr(request.user, "org", None)
        if not org:
            return Response({"error": "User not linked to any organization"}, status=status.HTTP_400_BAD_REQUEST)

        try:
            integration = Integration.objects.get(org=org, provider=provider)
        except Integration.DoesNotExist:
            return Response({"status": "not_connected"}, status=status.HTTP_404_NOT_FOUND)

        integration.delete()
        return Response({"status": "disconnected"})


class GmailMessagesView(APIView):
    """Fetch Gmail messages and replies."""
    permission_classes = [IsAuthenticated]

    def get(self, request):
        org = getattr(request.user, "org", None)
        if not org:
            return Response({"error": "User not linked to any organization"}, status=status.HTTP_400_BAD_REQUEST)

        try:
            integration = Integration.objects.get(org=org, provider="gmail")
        except Integration.DoesNotExist:
            return Response({"error": "Gmail not connected"}, status=status.HTTP_400_BAD_REQUEST)

        try:
            from integrations.gmail_utils import fetch_gmail_messages
            query = request.query_params.get("q", "")
            max_results = int(request.query_params.get("max_results", 50))
            messages = fetch_gmail_messages(integration, query=query, max_results=max_results)
            return Response({"messages": messages})
        except Exception as e:
            return Response({"error": str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


class GmailRepliesView(APIView):
    """Fetch replies for a Gmail thread."""
    permission_classes = [IsAuthenticated]

    def get(self, request, thread_id):
        org = getattr(request.user, "org", None)
        if not org:
            return Response({"error": "User not linked to any organization"}, status=status.HTTP_400_BAD_REQUEST)

        try:
            integration = Integration.objects.get(org=org, provider="gmail")
        except Integration.DoesNotExist:
            return Response({"error": "Gmail not connected"}, status=status.HTTP_400_BAD_REQUEST)

        try:
            from integrations.gmail_utils import fetch_gmail_replies
            replies = fetch_gmail_replies(integration, thread_id)
            return Response({"replies": replies})
        except Exception as e:
            return Response({"error": str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
