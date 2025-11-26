from django.contrib import admin
from integrations import models
# Register your models here.

@admin.register(models.Integration)
class IntegrationAdmin(admin.ModelAdmin):
    list_display = ("org", "provider", "access_token", "refresh_token", "expires_at")
    list_filter = ("provider",)