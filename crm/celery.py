import os
from celery import Celery

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "crm.settings")

app = Celery("crm")

# Load config from Django settings, using CELERY_ prefix
app.config_from_object("django.conf:settings", namespace="CELERY")

# Autodiscover tasks in all installed apps
app.autodiscover_tasks()

# Optional: periodic tasks
from celery.schedules import crontab

app.conf.beat_schedule = {
    # Daily enrichment task - runs at 2 AM UTC
    "daily-lead-enrichment": {
        "task": "campaigns.tasks.daily_enrich_leads",
        "schedule": crontab(hour=2, minute=0),
    },
}
