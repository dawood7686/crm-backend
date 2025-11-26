from uuid import uuid4
from django.db import models
from users.models import BaseModel

# Create your models here.

class ActivityTimeline(BaseModel):
    lead = models.ForeignKey("campaigns.Lead", related_name="activities", on_delete=models.CASCADE)
    step = models.ForeignKey("campaigns.SequenceStep", on_delete=models.CASCADE, null=True)
    payload = models.JSONField(default=dict)

class AIDraft(BaseModel):
    lead = models.ForeignKey("campaigns.Lead", related_name="ai_drafts", on_delete=models.CASCADE)
    variant = models.CharField(max_length=20)  # concise, detailed, meeting
    subject = models.CharField(max_length=255)
    body = models.TextField()
