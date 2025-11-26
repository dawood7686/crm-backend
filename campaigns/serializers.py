from rest_framework import serializers

from activities.models import ActivityTimeline
from campaigns.models import Campaign, Lead, LeadEmail, SequenceStep


class CampaignSerializer(serializers.ModelSerializer):
    class Meta:
        model = Campaign
        fields = ["id", "name", "created_at", "updated_at"]
        read_only_fields = ["id", "created_at", "updated_at"]


class LeadSerializer(serializers.ModelSerializer):
    campaign_name = serializers.CharField(source="campaign.name", read_only=True)

    class Meta:
        model = Lead
        fields = [
            "id",
            "campaign",
            "campaign_name",
            "first_name",
            "last_name",
            "email",
            "company",
            "linkedin_url",
            "website",
            "phone",
            "status",
            "last_contacted_at",
            "created_at",
            "updated_at",
        ]
        read_only_fields = ["id", "campaign_name", "created_at", "updated_at", "last_contacted_at"]


class SequenceStepSerializer(serializers.ModelSerializer):
    campaign_name = serializers.CharField(source="campaign.name", read_only=True)

    class Meta:
        model = SequenceStep
        fields = ["id", "campaign", "campaign_name", "order", "action", "wait_days", "created_at", "updated_at"]
        read_only_fields = ["id", "campaign_name", "created_at", "updated_at"]


class LeadEmailSerializer(serializers.ModelSerializer):
    lead_name = serializers.SerializerMethodField()
    lead_email = serializers.CharField(source="lead.email", read_only=True)

    class Meta:
        model = LeadEmail
        fields = [
            "id",
            "lead",
            "lead_name",
            "lead_email",
            "subject",
            "body",
            "preview",
            "status",
            "sent_at",
            "created_at",
            "updated_at",
        ]
        read_only_fields = ["id", "lead_name", "lead_email", "sent_at", "created_at", "updated_at"]

    def get_lead_name(self, obj):
        full_name = f"{obj.lead.first_name} {obj.lead.last_name}".strip()
        return full_name or obj.lead.email


class ActivityTimelineSerializer(serializers.ModelSerializer):
    lead_email = serializers.CharField(source="lead.email", read_only=True)
    campaign_name = serializers.CharField(source="lead.campaign.name", read_only=True)

    class Meta:
        model = ActivityTimeline
        fields = [
            "id",
            "lead",
            "lead_email",
            "campaign_name",
            "step",
            "payload",
            "created_at",
        ]
        read_only_fields = ["id", "lead_email", "campaign_name", "created_at"]


