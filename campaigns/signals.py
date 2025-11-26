from django.db.models.signals import post_save
from django.dispatch import receiver
from .models import Lead, LeadEmail
from .tasks import crawl_company_website
from .utils import personalize_template_copy
from agents.tasks import initiate_call_task
from users.models import OrganizationConfigurations

@receiver(post_save, sender=Lead)
def auto_enrich_lead(sender, instance, created, **kwargs):
    if created:
        # Trigger Celery task asynchronously
        print("Going to crawl")
        crawl_company_website.delay(instance.id)
        
        # Auto-generate email draft for the new lead
        try:
            org_config = OrganizationConfigurations.objects.filter(organization=instance.org).first()
            if not org_config:
                print(f"No organization config found for org: {instance.org}")
                return
            
            if not org_config.product_name:
                print(f"No product_name configured for org: {instance.org}")
                return
            
            if not instance.email:
                print(f"No email for lead: {instance.id}")
                return
            
            # Check if a draft already exists for this lead
            existing_draft = LeadEmail.objects.filter(lead=instance, status="draft").first()
            if existing_draft:
                print(f"Draft already exists for lead: {instance.id}")
                return
            
            # Generate email draft based on product information
            company_name = org_config.company_name or "our company"
            product_name = org_config.product_name
            product_description = org_config.product_description or ""
            
            # Default subject template
            subject_template = f"Quick intro from {company_name}"
            
            # Default email body template using product information
            email_body_template = f"""Hi {{first_name}},

I'm reaching out from {company_name} about {product_name}.

{product_description if product_description else f'We help companies like yours with {product_name}.'}

Would you be open to a quick conversation to see if this could be a good fit for your team?

Best regards"""
            
            rendered_subject = personalize_template_copy(subject_template, instance)
            rendered_body = personalize_template_copy(email_body_template, instance)
            
            email_draft = LeadEmail.objects.create(
                lead=instance,
                subject=rendered_subject,
                body=rendered_body,
                preview=rendered_body,
                status="draft",
                meta={
                    "source": "auto_generated",
                    "product": product_name,
                    "company": company_name,
                },
            )
            print(f"Successfully created email draft {email_draft.id} for lead {instance.id}")
        except Exception as e:
            import traceback
            print(f"Error auto-generating email draft: {e}")
            print(traceback.format_exc())
        
        if not instance.phone:
            return

            # You can customize the agent name or assign based on rules
        agent_name = "AutoDialer"

        initiate_call_task.delay(
            lead_id=str(instance.id),
            phone_number=instance.phone,
            agent_name=agent_name,
        )
