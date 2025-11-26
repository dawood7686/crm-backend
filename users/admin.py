from django.contrib import admin
from users import models
# Register your models here.

@admin.register(models.Organization)
class OrganizationAdmin(admin.ModelAdmin):
    list_display = ("id", "name", "description", "created_at", "updated_at")
    fields = ("name", "description")

@admin.register(models.User)
class UserAdmin(admin.ModelAdmin):
    list_display = ("id", "username", "org", "role", "created_at", "updated_at")
    fields = ("username", "org", "role")

@admin.register(models.OrganizationConfigurations)
class OrganizationConfigurationsAdmin(admin.ModelAdmin):
    list_display = ("id", "organization", )
    fields = ("id", "organization", "ai_model", "ai_model_api_key", "google_client_id", "google_client_secret", "firecrawl_api_key", "slack_client_id", "slack_client_secret", "hubspot_client_id", "hubspot_client_secret", "created_at", "updated_at")
    list_filter = ("organization",)
    readonly_fields = ("id", "created_at", "updated_at")


