from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.permissions import AllowAny
from django.shortcuts import get_object_or_404
from campaigns.models import Lead
from .models import Call


class CallWebhookView(APIView):
    permission_classes = [AllowAny]  # since it’s internal, you may restrict by IP later

    def post(self, request, *args, **kwargs):
        """
        Webhook receiver for call summaries from FastAPI.
        Expected payload:
        {
            "call_sid": "...",
            "recording_url": "https://...",
            "summary": "..."
        }
        """
        data = request.data
        call_sid = data.get("call_sid")
        recording_url = data.get("recording_url")
        summary = data.get("summary")
        lead_id = data.get("lead_id")

        if not all([call_sid, recording_url, summary]):
            return Response({"error": "Missing required fields"}, status=400)

        lead = None
        if lead_id:
            from campaigns.models import Lead
            lead = get_object_or_404(Lead, id=lead_id)

        call, created = Call.objects.update_or_create(
            call_sid=call_sid,
            defaults={
                "lead": lead,
                "recording_url": recording_url,
                "summary": summary,
            }
        )

        # Optionally trigger any follow-up logic or notification
        # e.g., notify SDR, send Slack message, etc.

        return Response({
            "status": "success",
            "message": "Call summary saved successfully",
            "call_id": call.id
        })
from django.shortcuts import render

# Create your views here.
