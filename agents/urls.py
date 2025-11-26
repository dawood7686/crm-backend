from django.urls import path
from .views import CallWebhookView

urlpatterns = [
    path("calls/webhook/", CallWebhookView.as_view(), name="call-webhook"),
]
