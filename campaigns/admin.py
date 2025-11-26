from django.contrib import admin
from campaigns.models import Campaign, Lead, SequenceStep

@admin.register(Campaign)
class CampaignAdmin(admin.ModelAdmin):
    list_display = ("org", "name",)
    list_filter = ("org",)

@admin.register(Lead)
class LeadAdmin(admin.ModelAdmin):
    list_display = ("first_name", "last_name", "website", "phone", "enriched", "status")
    list_display_links = ("first_name",)
    list_filter = ("status",)

@admin.register(SequenceStep)
class SequenceStepAdmin(admin.ModelAdmin):
    list_display = ("campaign", "order")