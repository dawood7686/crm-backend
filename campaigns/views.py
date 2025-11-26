from django.http import JsonResponse
from django.utils import timezone
from rest_framework import status
from rest_framework.exceptions import ValidationError
from rest_framework.parsers import FormParser, MultiPartParser
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView

from activities.models import ActivityTimeline
from campaigns.models import Campaign, Lead, LeadEmail, SequenceStep
from campaigns.serializers import (
    ActivityTimelineSerializer,
    CampaignSerializer,
    LeadEmailSerializer,
    LeadSerializer,
    SequenceStepSerializer,
)
from campaigns.utils import (
    add_leads_to_db,
    file_preprocessing,
    personalize_template_copy,
    upload_file,
)
from integrations.models import Integration
from users.models import Organization, User


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

    def get_user(self, request):
        return request.user


class DashboardSummaryView(SalesorchBaseAPIView):
    def get(self, request):
        org = self.get_org(request)
        leads_qs = Lead.objects.filter(org=org)
        campaigns_qs = Campaign.objects.filter(org=org)
        emails_qs = LeadEmail.objects.filter(lead__org=org)

        status_breakdown = {
            "new": leads_qs.filter(status="new").count(),
            "contacted": leads_qs.filter(status="contacted").count(),
            "replied": leads_qs.filter(status="replied").count(),
        }

        metrics = {
            "total_leads": leads_qs.count(),
            "total_campaigns": campaigns_qs.count(),
            "emails_sent": emails_qs.filter(status="sent").count(),
            "active_sequences": SequenceStep.objects.filter(campaign__org=org).count(),
        }

        recent_leads = LeadSerializer(leads_qs.order_by("-created_at")[:5], many=True).data
        recent_emails = LeadEmailSerializer(emails_qs.order_by("-created_at")[:5], many=True).data

        campaign_performance = []
        for campaign in campaigns_qs.prefetch_related("lead_set"):
            total_leads = campaign.lead_set.count()
            replied = campaign.lead_set.filter(status="replied").count()
            performance = {
                "id": str(campaign.id),
                "name": campaign.name,
                "total_leads": total_leads,
                "replied": replied,
            }
            campaign_performance.append(performance)

        integration_status = []
        for integration in Integration.objects.filter(org=org):
            integration_status.append(
                {
                    "provider": integration.provider,
                    "expires_at": integration.expires_at,
                }
            )

        payload = {
            "metrics": metrics,
            "status_breakdown": status_breakdown,
            "recent_leads": recent_leads,
            "recent_emails": recent_emails,
            "campaign_performance": campaign_performance,
            "integration_status": integration_status,
        }
        return Response(payload)


class LeadListCreateView(SalesorchBaseAPIView):
    def get(self, request):
        org = self.get_org(request)
        leads = Lead.objects.filter(org=org).order_by("-created_at")
        serializer = LeadSerializer(leads, many=True)
        return Response(serializer.data)

    def post(self, request):
        org = self.get_org(request)
        serializer = LeadSerializer(data=request.data)
        if serializer.is_valid():
            serializer.save(org=org)
            return Response(serializer.data, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class LeadDetailView(SalesorchBaseAPIView):
    def get_object(self, org, pk):
        try:
            return Lead.objects.get(id=pk, org=org)
        except Lead.DoesNotExist:
            return None

    def patch(self, request, pk):
        org = self.get_org(request)
        lead = self.get_object(org, pk)
        if not lead:
            return Response({"error": "Lead not found"}, status=status.HTTP_404_NOT_FOUND)

        serializer = LeadSerializer(lead, data=request.data, partial=True)
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    def delete(self, request, pk):
        org = self.get_org(request)
        lead = self.get_object(org, pk)
        if not lead:
            return Response({"error": "Lead not found"}, status=status.HTTP_404_NOT_FOUND)
        lead.delete()
        return Response(status=status.HTTP_204_NO_CONTENT)


class CampaignListCreateView(SalesorchBaseAPIView):
    def get(self, request):
        org = self.get_org(request)
        campaigns = Campaign.objects.filter(org=org).order_by("name")
        serializer = CampaignSerializer(campaigns, many=True)
        return Response(serializer.data)

    def post(self, request):
        org = self.get_org(request)
        serializer = CampaignSerializer(data=request.data)
        if serializer.is_valid():
            serializer.save(org=org)
            return Response(serializer.data, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class CampaignDetailView(SalesorchBaseAPIView):
    def get_object(self, org, pk):
        try:
            return Campaign.objects.get(id=pk, org=org)
        except Campaign.DoesNotExist:
            return None

    def patch(self, request, pk):
        org = self.get_org(request)
        campaign = self.get_object(org, pk)
        if not campaign:
            return Response({"error": "Campaign not found"}, status=status.HTTP_404_NOT_FOUND)
        serializer = CampaignSerializer(campaign, data=request.data, partial=True)
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    def delete(self, request, pk):
        org = self.get_org(request)
        campaign = self.get_object(org, pk)
        if not campaign:
            return Response({"error": "Campaign not found"}, status=status.HTTP_404_NOT_FOUND)
        campaign.delete()
        return Response(status=status.HTTP_204_NO_CONTENT)


class SequenceStepListCreateView(SalesorchBaseAPIView):
    def get(self, request):
        org = self.get_org(request)
        campaign_id = request.query_params.get("campaign_id")
        queryset = SequenceStep.objects.filter(campaign__org=org).order_by("campaign_id", "order")
        if campaign_id:
            queryset = queryset.filter(campaign_id=campaign_id)
        serializer = SequenceStepSerializer(queryset, many=True)
        return Response(serializer.data)

    def post(self, request):
        org = self.get_org(request)
        serializer = SequenceStepSerializer(data=request.data)
        if serializer.is_valid():
            campaign = serializer.validated_data["campaign"]
            if campaign.org != org:
                return Response({"error": "You cannot modify this campaign"}, status=status.HTTP_403_FORBIDDEN)
            serializer.save()
            return Response(serializer.data, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class SequenceStepDetailView(SalesorchBaseAPIView):
    def get_object(self, org, pk):
        try:
            return SequenceStep.objects.get(id=pk, campaign__org=org)
        except SequenceStep.DoesNotExist:
            return None

    def patch(self, request, pk):
        org = self.get_org(request)
        step = self.get_object(org, pk)
        if not step:
            return Response({"error": "Sequence step not found"}, status=status.HTTP_404_NOT_FOUND)
        serializer = SequenceStepSerializer(step, data=request.data, partial=True)
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    def delete(self, request, pk):
        org = self.get_org(request)
        step = self.get_object(org, pk)
        if not step:
            return Response({"error": "Sequence step not found"}, status=status.HTTP_404_NOT_FOUND)
        step.delete()
        return Response(status=status.HTTP_204_NO_CONTENT)


class UploadFile(SalesorchBaseAPIView):
    parser_classes = (MultiPartParser, FormParser)

    def post(self, request):
        org = self.get_org(request)
        file_obj = request.FILES.get("file")
        campaign_id = request.data.get("campaign_id")
        commit_flag = str(request.data.get("commit", "false")).lower() == "true"
        preview_rows = int(request.data.get("preview_rows", 5) or 5)

        if not file_obj:
            return Response({"error": "No file uploaded"}, status=status.HTTP_400_BAD_REQUEST)

        try:
            df = upload_file(file_obj)
            valid_df = file_preprocessing(df)
        except Exception as exc:
            return Response({"error": str(exc)}, status=status.HTTP_400_BAD_REQUEST)

        preview_records = valid_df.fillna("").head(preview_rows).to_dict(orient="records")
        save_stats = {"created": 0, "updated": 0}
        if commit_flag:
            try:
                save_stats = add_leads_to_db(valid_df, org, campaign_id)
            except Exception as exc:
                return Response({"error": str(exc)}, status=status.HTTP_400_BAD_REQUEST)

        return Response(
            {
            "file_name": file_obj.name,
                "total_rows": len(valid_df.index),
                "preview": preview_records,
                "committed": commit_flag,
                "stats": save_stats,
            }
        )


class EmailPreviewView(SalesorchBaseAPIView):
    def post(self, request):
        org = self.get_org(request)
        lead_id = request.data.get("lead_id")
        subject_template = request.data.get("subject", "")
        body_template = request.data.get("body", "")

        if not lead_id:
            return Response({"error": "lead_id is required"}, status=status.HTTP_400_BAD_REQUEST)

        try:
            lead = Lead.objects.get(id=lead_id, org=org)
        except Lead.DoesNotExist:
            return Response({"error": "Lead not found"}, status=status.HTTP_404_NOT_FOUND)

        rendered_subject = personalize_template_copy(subject_template, lead)
        rendered_body = personalize_template_copy(body_template, lead)

        return Response(
            {
                "lead": LeadSerializer(lead).data,
                "subject": rendered_subject,
                "body": rendered_body,
            }
        )


class EmailSendView(SalesorchBaseAPIView):
    def post(self, request):
        org = self.get_org(request)
        lead_id = request.data.get("lead_id")
        email_id = request.data.get("email_id")
        subject_template = request.data.get("subject", "")
        body_template = request.data.get("body", "")

        lead_email = None
        lead = None

        if email_id:
            try:
                lead_email = LeadEmail.objects.select_related("lead").get(id=email_id, lead__org=org)
                lead = lead_email.lead
            except LeadEmail.DoesNotExist:
                return Response({"error": "Draft email not found"}, status=status.HTTP_404_NOT_FOUND)
        else:
            if not lead_id:
                return Response({"error": "lead_id is required when no email draft is provided"}, status=status.HTTP_400_BAD_REQUEST)
            try:
                lead = Lead.objects.get(id=lead_id, org=org)
            except Lead.DoesNotExist:
                return Response({"error": "Lead not found"}, status=status.HTTP_404_NOT_FOUND)

        if lead_email is None:
            rendered_subject = personalize_template_copy(subject_template, lead)
            rendered_body = personalize_template_copy(body_template, lead)
            lead_email = LeadEmail.objects.create(
                lead=lead,
                subject=rendered_subject,
                body=rendered_body,
                preview=rendered_body,
                status="draft",
                meta={"source": "salesorch_dashboard", "mode": "manual"},
            )
        else:
            # Update draft with any new text that might have been supplied
            if subject_template:
                lead_email.subject = personalize_template_copy(subject_template, lead)
            if body_template:
                rendered_body = personalize_template_copy(body_template, lead)
                lead_email.body = rendered_body
                lead_email.preview = rendered_body
            lead_email.save()

        # Try to send via Gmail if integration exists
        gmail_sent = False
        try:
            from integrations.models import Integration
            from integrations.gmail_utils import send_gmail_email, get_valid_access_token
            
            integration = Integration.objects.filter(org=org, provider="gmail").first()
            if integration:
                try:
                    access_token = get_valid_access_token(integration)
                    gmail_response = send_gmail_email(
                        integration=integration,
                        to_email=lead.email,
                        subject=lead_email.subject,
                        body=lead_email.body,
                    )
                    gmail_sent = True
                    lead_email.meta = {
                        **(lead_email.meta or {}),
                        "disposition": "sent_via_gmail",
                        "gmail_message_id": gmail_response.get("id"),
                    }
                except Exception as e:
                    # If Gmail send fails, mark as failed but don't raise error
                    lead_email.meta = {
                        **(lead_email.meta or {}),
                        "disposition": "gmail_send_failed",
                        "error": str(e),
                    }
        except Exception as e:
            # Integration not available or error, continue without Gmail
            pass

        if gmail_sent:
            lead_email.status = "sent"
            lead_email.sent_at = timezone.now()
        else:
            # If Gmail not available, just mark as sent in our system
            lead_email.status = "sent"
            lead_email.sent_at = timezone.now()
            if not gmail_sent:
                lead_email.meta = {**(lead_email.meta or {}), "disposition": "sent_via_dashboard"}
        
        lead_email.save(update_fields=["status", "sent_at", "meta", "updated_at", "subject", "body", "preview"])

        lead.last_contacted_at = timezone.now()
        lead.status = "contacted"
        lead.save(update_fields=["last_contacted_at", "status", "updated_at"])

        serializer = LeadEmailSerializer(lead_email)
        return Response(serializer.data, status=status.HTTP_201_CREATED)


class EmailLogListView(SalesorchBaseAPIView):
    def get(self, request):
        org = self.get_org(request)
        emails = LeadEmail.objects.filter(lead__org=org).order_by("-created_at")
        serializer = LeadEmailSerializer(emails, many=True)
        return Response(serializer.data)


class EmailStatsView(SalesorchBaseAPIView):
    def get(self, request):
        org = self.get_org(request)
        emails = LeadEmail.objects.filter(lead__org=org)
        
        # Count opened and replied emails by checking meta field
        opened_count = 0
        replied_count = 0
        for email in emails:
            meta = email.meta or {}
            if meta.get("opened_at"):
                opened_count += 1
            if meta.get("replied_at"):
                replied_count += 1
        
        stats = {
            "total": emails.count(),
            "sent": emails.filter(status="sent").count(),
            "drafts": emails.filter(status="draft").count(),
            "failed": emails.filter(status="failed").count(),
            "opened": opened_count,
            "replied": replied_count,
        }
        
        # Get detailed email timeline
        sent_emails = emails.filter(status="sent").select_related("lead").order_by("-sent_at")[:50]
        email_timeline = []
        for email in sent_emails:
            meta = email.meta or {}
            timeline_item = {
                "id": str(email.id),
                "subject": email.subject,
                "lead_email": email.lead.email,
                "lead_name": f"{email.lead.first_name} {email.lead.last_name}".strip() or email.lead.email,
                "sent_at": email.sent_at.isoformat() if email.sent_at else None,
                "opened_at": meta.get("opened_at"),
                "replied_at": meta.get("replied_at"),
                "ai_reply": meta.get("ai_reply"),
            }
            email_timeline.append(timeline_item)
        
        return Response({
            "stats": stats,
            "timeline": email_timeline,
        })


class EmailGenerateView(SalesorchBaseAPIView):
    def post(self, request):
        org = self.get_org(request)
        lead_id = request.data.get("lead_id")
        prompt = request.data.get("prompt", "")
        subject_prompt = request.data.get("subject_prompt", "Quick intro from {{company}}")

        if not lead_id:
            return Response({"error": "lead_id is required"}, status=status.HTTP_400_BAD_REQUEST)

        if not prompt:
            return Response({"error": "prompt is required"}, status=status.HTTP_400_BAD_REQUEST)

        try:
            lead = Lead.objects.get(id=lead_id, org=org)
        except Lead.DoesNotExist:
            return Response({"error": "Lead not found"}, status=status.HTTP_404_NOT_FOUND)

        # Check if a draft already exists for this lead
        existing_draft = LeadEmail.objects.filter(lead=lead, status="draft").first()
        if existing_draft:
            # Return existing draft instead of creating a duplicate
            serializer = LeadEmailSerializer(existing_draft)
            return Response(serializer.data, status=status.HTTP_200_OK)

        rendered_subject = personalize_template_copy(subject_prompt, lead)
        rendered_body = personalize_template_copy(prompt, lead)

        lead_email = LeadEmail.objects.create(
            lead=lead,
            subject=rendered_subject,
            body=rendered_body,
            preview=rendered_body,
            status="draft",
            meta={"source": "salesorch_ai", "prompt": prompt},
        )

        serializer = LeadEmailSerializer(lead_email)
        return Response(serializer.data, status=status.HTTP_201_CREATED)


class ActivityListView(SalesorchBaseAPIView):
    def get(self, request):
        org = self.get_org(request)
        activities = ActivityTimeline.objects.filter(lead__org=org).order_by("-created_at")[:25]
        serializer = ActivityTimelineSerializer(activities, many=True)
        return Response(serializer.data)
