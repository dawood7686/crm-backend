from celery import shared_task
from django.utils import timezone
from users.models import OrganizationConfigurations
from .models import Lead
from firecrawl import Firecrawl
import requests


@shared_task
def crawl_company_website(lead_id):
    lead = Lead.objects.get(id=lead_id)
    org_config = OrganizationConfigurations.objects.filter(organization=lead.org).last()
    firecrawl = Firecrawl(api_key=org_config.firecrawl_api_key)
    company_url = lead.website
    if not company_url:
        return {"status": "no_url", "lead_id": str(lead.id)}

    if not company_url.startswith("http"):
        company_url = f"https://{company_url}"

    try:
        schema = {
            "type": "object",
            "properties": {"description": {"type": "string"}, "company profile": {"type": "string"}, "recent news": {"type": "string"}, "social links": {"type": "string"}},
            "required": ["description"],
        }

        res = firecrawl.extract(
            urls=[company_url],
            prompt="Extract the page description, company profile, recent news and social links",
            allow_external_links=False,
            ignore_invalid_urls=True,
            schema=schema,
        )

        # Save enrichment data to lead
        lead.enriched = dict(res)
        lead.save()
        return {"status": "success", "lead_id": str(lead.id)}
    except Exception as e:
        return {"status": "error", "lead_id": str(lead.id), "error": str(e)}


@shared_task
def daily_enrich_leads():
    """
    Daily task to enrich leads that haven't been enriched yet or need re-enrichment.
    Processes leads that have a website but no enrichment data or stale enrichment.
    """
    from django.db.models import Q
    
    # Get leads that have a website but no enrichment or empty enrichment
    leads_to_enrich = Lead.objects.filter(
        Q(website__isnull=False) & ~Q(website=""),
        Q(enriched__isnull=True) | Q(enriched={})
    )[:50]  # Process up to 50 leads per run to avoid overwhelming the system
    
    enriched_count = 0
    error_count = 0
    
    for lead in leads_to_enrich:
        try:
            org_config = OrganizationConfigurations.objects.filter(organization=lead.org).first()
            if not org_config or not org_config.firecrawl_api_key:
                continue
            
            # Trigger async enrichment
            crawl_company_website.delay(str(lead.id))
            enriched_count += 1
        except Exception as e:
            error_count += 1
            continue
    
    return {
        "status": "completed",
        "processed": enriched_count,
        "errors": error_count,
        "total_found": leads_to_enrich.count()
    }

