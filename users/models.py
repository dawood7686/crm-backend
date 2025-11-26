from datetime import datetime

from django.contrib.auth.models import AbstractUser
from django.db import models
from uuid import uuid4

from users.enums import AIModelPlatformChoices


# Create your models here.
class BaseModel(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid4)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    class Meta:
        abstract = True

class Organization(BaseModel):
    name = models.CharField(max_length=255)
    description = models.TextField(blank=True)

class User(AbstractUser, BaseModel):
    org = models.ForeignKey(Organization, on_delete=models.CASCADE, null=True, blank=True)
    role = models.CharField(choices=[("admin","Admin"),("sdr","SDR")])

# class UserAIModelConfig(BaseModel):
#     user = models.ForeignKey(User, on_delete=models.CASCADE, related_name="ai_configs")
#     platform = models.CharField(
#         max_length=20,
#         choices=AIModelPlatformChoices.choices(),
#         default=AIModelPlatformChoices.OPENAI.value,
#     )
#
#     api_key = models.CharField(max_length=255)
#
#     def __str__(self):
#         return f"{self.user} - {self.platform}"

class OrganizationConfigurations(BaseModel):
    organization = models.ForeignKey(Organization, on_delete=models.CASCADE, related_name="configurations")

    # Company Information
    company_name = models.CharField(max_length=255, help_text="Company name", null=True, blank=True)
    company_details = models.TextField(help_text="Company description and details", null=True, blank=True)
    
    # Product Information
    product_name = models.CharField(max_length=255, help_text="Product/Service name", null=True, blank=True)
    product_description = models.TextField(help_text="Product description and features", null=True, blank=True)

    # AI model
    ai_model = models.CharField(
        max_length=20,
        choices=AIModelPlatformChoices.choices(),
        default=AIModelPlatformChoices.OPENAI.value,
    )
    ai_model_api_key = models.CharField(max_length=255, help_text="AI Model API key", null=True, blank=True)

    #Google App
    google_client_id = models.CharField(max_length=255, help_text="Google Client ID", null=True, blank=True)
    google_client_secret = models.CharField(max_length=255, help_text="Google client secret", null=True, blank=True)

    #firecrawl
    firecrawl_api_key = models.CharField(max_length=255, help_text="FC API key", null=True, blank=True)

    #slack
    slack_client_id = models.CharField(max_length=255, help_text="Slack Client ID", null=True, blank=True)
    slack_client_secret = models.CharField(max_length=255, help_text="Slack client secret", null=True, blank=True)

    #hubspot
    hubspot_client_id = models.CharField(max_length=255, help_text="Hubspot Client ID", null=True, blank=True)
    hubspot_client_secret = models.CharField(max_length=255, help_text="Hubspot client secret", null=True, blank=True)

    class Meta:
        verbose_name = "Organization Configuration"

