from rest_framework import status
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework.exceptions import ValidationError

from users.models import Organization, OrganizationConfigurations
from users.enums import AIModelPlatformChoices


class SalesorchBaseAPIView(APIView):
    """
    Base API view that scopes every request to the authenticated user's organization.
    """

    permission_classes = (IsAuthenticated,)

    def get_org(self, request):
        org = getattr(request.user, "org", None)
        if not org:
            raise ValidationError("User is not associated with any organization.")
        return org


class OrganizationConfigView(SalesorchBaseAPIView):
    """
    Get and update organization configurations (API keys, etc.)
    """

    def get(self, request):
        org = self.get_org(request)
        config = OrganizationConfigurations.objects.filter(organization=org).first()
        
        if not config:
            return Response({
                "company_name": "",
                "company_details": "",
                "product_name": "",
                "product_description": "",
                "ai_model": AIModelPlatformChoices.OPENAI.value,
                "ai_model_api_key": "",
                "google_client_id": "",
                "google_client_secret": "",
                "firecrawl_api_key": "",
                "slack_client_id": "",
                "slack_client_secret": "",
                "hubspot_client_id": "",
                "hubspot_client_secret": "",
            })
        
        return Response({
            "company_name": config.company_name or "",
            "company_details": config.company_details or "",
            "product_name": config.product_name or "",
            "product_description": config.product_description or "",
            "ai_model": config.ai_model,
            "ai_model_api_key": config.ai_model_api_key or "",
            "google_client_id": config.google_client_id or "",
            "google_client_secret": config.google_client_secret or "",
            "firecrawl_api_key": config.firecrawl_api_key or "",
            "slack_client_id": config.slack_client_id or "",
            "slack_client_secret": config.slack_client_secret or "",
            "hubspot_client_id": config.hubspot_client_id or "",
            "hubspot_client_secret": config.hubspot_client_secret or "",
        })

    def post(self, request):
        org = self.get_org(request)
        data = request.data
        
        config, created = OrganizationConfigurations.objects.update_or_create(
            organization=org,
            defaults={
                "company_name": data.get("company_name", ""),
                "company_details": data.get("company_details", ""),
                "product_name": data.get("product_name", ""),
                "product_description": data.get("product_description", ""),
                "ai_model": data.get("ai_model", AIModelPlatformChoices.OPENAI.value),
                "ai_model_api_key": data.get("ai_model_api_key", ""),
                "google_client_id": data.get("google_client_id", ""),
                "google_client_secret": data.get("google_client_secret", ""),
                "firecrawl_api_key": data.get("firecrawl_api_key", ""),
                "slack_client_id": data.get("slack_client_id", ""),
                "slack_client_secret": data.get("slack_client_secret", ""),
                "hubspot_client_id": data.get("hubspot_client_id", ""),
                "hubspot_client_secret": data.get("hubspot_client_secret", ""),
            }
        )
        
        return Response({
            "status": "saved",
            "company_name": config.company_name or "",
            "company_details": config.company_details or "",
            "product_name": config.product_name or "",
            "product_description": config.product_description or "",
            "ai_model": config.ai_model,
            "ai_model_api_key": config.ai_model_api_key or "",
            "google_client_id": config.google_client_id or "",
            "google_client_secret": config.google_client_secret or "",
            "firecrawl_api_key": config.firecrawl_api_key or "",
            "slack_client_id": config.slack_client_id or "",
            "slack_client_secret": config.slack_client_secret or "",
            "hubspot_client_id": config.hubspot_client_id or "",
            "hubspot_client_secret": config.hubspot_client_secret or "",
        }, status=status.HTTP_200_OK)
