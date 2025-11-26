from django.db import models
from users.models import BaseModel, Organization


# Create your models here.

class Integration(BaseModel):
    PROVIDER_CHOICES = [
        ("gmail", "Gmail"),
        ("hubspot", "HubSpot"),
    ]

    org = models.ForeignKey(Organization, on_delete=models.CASCADE)
    provider = models.CharField(max_length=20, choices=PROVIDER_CHOICES)
    access_token = models.TextField()
    refresh_token = models.TextField()
    expires_at = models.DateTimeField()