# crm/calls/tasks.py
from celery import shared_task
import requests
from django.conf import settings

@shared_task(bind=True, max_retries=3)
def initiate_call_task(self, lead_id, phone_number, agent_name):
    """
    Sends call request to FastAPI calling service asynchronously.
    """
    try:
        '''{
            "lead_id": 0,
            "lead_name": "string",
            "company": "string",
            "phone_number": "string",
            "product": "string",
            "goal": "string"
        }'''
        data = {
            "lead_id": f"{lead_id}",
            "lead_name": "test",
            "company": "test",
            "product": "test",
            "goal": "test",
            "phone_number": phone_number,
            # "webhook_url": f"{settings.BACKEND_URL}/api/v1/calls/webhook/",
        }

        fastapi_url = f"{settings.CALLING_SERVICE_URL}/call/initiate/"
        # fastapi_url = "http://127.0.0.1:8001/call/initiate"
        print(fastapi_url)
        response = requests.post(fastapi_url, json=data)
        response.raise_for_status()

        return {"status": "success", "response": response.json()}

    except requests.exceptions.RequestException as e:
        self.retry(exc=e, countdown=10)
