from django.db import models
from django.contrib.auth import get_user_model

User = get_user_model()


class Call(models.Model):
    lead = models.ForeignKey("campaigns.Lead", on_delete=models.CASCADE, related_name="calls")
    user = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True)
    call_sid = models.CharField(max_length=128, unique=True)
    recording_url = models.URLField()
    summary = models.TextField(blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        lead_label = self.lead.email or f"{self.lead.first_name} {self.lead.last_name}".strip()
        return f"Call with {lead_label} ({self.call_sid})"
