from django.urls import path

from campaigns import views

urlpatterns = [
    path("summary/", views.DashboardSummaryView.as_view(), name="campaign-summary"),
    path("leads/", views.LeadListCreateView.as_view(), name="lead-list-create"),
    path("leads/<uuid:pk>/", views.LeadDetailView.as_view(), name="lead-detail"),
    path("campaigns/", views.CampaignListCreateView.as_view(), name="campaign-list-create"),
    path("campaigns/<uuid:pk>/", views.CampaignDetailView.as_view(), name="campaign-detail"),
    path("sequences/", views.SequenceStepListCreateView.as_view(), name="sequence-list-create"),
    path("sequences/<uuid:pk>/", views.SequenceStepDetailView.as_view(), name="sequence-detail"),
    path("upload_file/", views.UploadFile.as_view(), name="lead-upload"),
    path("emails/", views.EmailLogListView.as_view(), name="email-log"),
    path("emails/stats/", views.EmailStatsView.as_view(), name="email-stats"),
    path("emails/preview/", views.EmailPreviewView.as_view(), name="email-preview"),
    path("emails/generate/", views.EmailGenerateView.as_view(), name="email-generate"),
    path("emails/send/", views.EmailSendView.as_view(), name="email-send"),
    path("activities/", views.ActivityListView.as_view(), name="activity-list"),
]