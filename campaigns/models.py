from django.db import models
from django.utils import timezone

from users.models import BaseModel, Organization


class Campaign(BaseModel):
    org = models.ForeignKey(Organization, on_delete=models.CASCADE)
    name = models.CharField(max_length=255)


class Lead(BaseModel):
    org = models.ForeignKey(Organization, on_delete=models.CASCADE)
    campaign = models.ForeignKey("campaigns.Campaign", null=True, blank=True, on_delete=models.SET_NULL)
    first_name = models.CharField(max_length=120, blank=True)
    last_name = models.CharField(max_length=120, blank=True)
    email = models.EmailField()
    company = models.CharField(max_length=255, blank=True)
    linkedin_url = models.URLField(blank=True)
    website = models.URLField(blank=True)
    phone = models.CharField(max_length=50, blank=True)
    enriched = models.JSONField(default=dict, blank=True)
    status = models.CharField(
        max_length=20,
        choices=[("new", "New"), ("contacted", "Contacted"), ("replied", "Replied")],
        default="new",
    )
    last_contacted_at = models.DateTimeField(null=True, blank=True)


class SequenceStep(BaseModel):
    campaign = models.ForeignKey(Campaign, related_name="steps", on_delete=models.CASCADE)
    order = models.PositiveIntegerField()
    action = models.CharField(max_length=20, choices=[("send_email", "Send Email"), ("wait", "Wait")])
    wait_days = models.IntegerField(default=0)


class LeadEmail(BaseModel):
    STATUS_CHOICES = [
        ("draft", "Draft"),
        ("sent", "Sent"),
        ("failed", "Failed"),
    ]

    lead = models.ForeignKey(Lead, related_name="emails", on_delete=models.CASCADE)
    subject = models.CharField(max_length=255)
    body = models.TextField()
    preview = models.TextField(blank=True)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default="draft")
    sent_at = models.DateTimeField(null=True, blank=True)
    meta = models.JSONField(default=dict, blank=True)

    def mark_sent(self, meta=None):
        self.status = "sent"
        self.sent_at = timezone.now()
        if meta is not None:
            self.meta = meta
        self.save(update_fields=["status", "sent_at", "meta", "updated_at"])

