import os
from typing import Dict, Optional

import pandas as pd
from django.conf import settings

from campaigns.models import Lead, Campaign


def upload_file(file_obj):
    upload_path = os.path.join(settings.BASE_DIR, "static", "uploads", file_obj.name)
    with open(upload_path, "wb+") as destination:
        for chunk in file_obj.chunks():
            destination.write(chunk)

    ext = os.path.splitext(file_obj.name)[1].lower()
    if ext == ".csv":
        df = pd.read_csv(upload_path)
    elif ext in [".xls", ".xlsx"]:
        df = pd.read_excel(upload_path)
    else:
        raise ValueError("Unsupported file type")

    return df


def file_preprocessing(df):
    df.columns = [c.strip().lower().replace(" ", "_") for c in df.columns]

    if "email" in df.columns:
        df = df.drop_duplicates(subset=["email"])
    return df


def add_leads_to_db(df: pd.DataFrame, org, campaign_id: Optional[str] = None) -> Dict[str, int]:
    df = df.copy()
    df.columns = df.columns.str.lower().str.strip()

    campaign = None
    if campaign_id:
        campaign = Campaign.objects.filter(id=campaign_id, org=org).last()
        if campaign is None:
            raise ValueError("Campaign not found for this organization")

    created, updated = 0, 0
    for _, row in df.iterrows():
        email = row.get("email")
        if not email:
            continue  # skip rows without email

        defaults = {
            "campaign": campaign,
            "org": org,
            "first_name": row.get("first_name") or row.get("firstname", ""),
            "last_name": row.get("last_name") or row.get("lastname", ""),
            "company": row.get("company", ""),
            "phone": row.get("phone", ""),
            "linkedin_url": row.get("linkedin") or row.get("linkedin_url", ""),
            "website": row.get("website", ""),
        }

        _, was_created = Lead.objects.update_or_create(
            email=email,
            org=org,
            defaults=defaults,
        )
        if was_created:
            created += 1
        else:
            updated += 1

    return {"created": created, "updated": updated}


def personalize_template_copy(template: str, lead: Lead) -> str:
    """
    Replaces simple merge tags in the template string with lead attributes.
    Supported tags: {{first_name}}, {{last_name}}, {{company}}, {{email}}
    """
    if not template:
        return ""

    replacements = {
        "{{first_name}}": lead.first_name or "",
        "{{last_name}}": lead.last_name or "",
        "{{company}}": lead.company or "",
        "{{email}}": lead.email or "",
    }

    rendered = template
    for token, value in replacements.items():
        rendered = rendered.replace(token, value)
    return rendered
