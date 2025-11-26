from django.urls import path

from .views import (
    GmailOAuthCallbackView,
    GoogleOAuthInitView,
    HubspotOAuthCallbackView,
    HubspotOAuthInitView,
    HubspotSyncContactsView,
    IntegrationStatusView,
    IntegrationDisconnectView,
    GmailMessagesView,
    GmailRepliesView,
)

urlpatterns = [
    path("google/callback/", GmailOAuthCallbackView.as_view(), name="gmail-oauth-callback"),
    path("google/login/", GoogleOAuthInitView.as_view(), name="gmail-oauth-callback"),
    path("google/messages/", GmailMessagesView.as_view(), name="gmail-messages"),
    path("google/threads/<str:thread_id>/replies/", GmailRepliesView.as_view(), name="gmail-replies"),
    path("hubspot/init/", HubspotOAuthInitView.as_view(), name="hubspot-init"),
    path("hubspot/callback/", HubspotOAuthCallbackView.as_view(), name="hubspot-callback"),
    path("hubspot/sync-contacts/", HubspotSyncContactsView.as_view(), name="hubspot-sync-contacts"),
    path("status/", IntegrationStatusView.as_view(), name="integration-status"),
    path("disconnect/<str:provider>/", IntegrationDisconnectView.as_view(), name="integration-disconnect"),
]
