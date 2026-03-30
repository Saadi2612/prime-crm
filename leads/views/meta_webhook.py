import json
import logging
import os

from django.conf import settings
from rest_framework import status
from rest_framework.permissions import AllowAny
from rest_framework.response import Response
from rest_framework.views import APIView
import requests
from django.utils.dateparse import parse_datetime
from leads.models import Lead, LeadStage

logger = logging.getLogger(__name__)

VERIFY_TOKEN = os.environ.get("META_VERIFY_TOKEN", "")


class MetaWebhookView(APIView):
    """
    Handles Meta (Facebook / Instagram) webhook callbacks.

    GET  — Webhook verification (hub.challenge handshake).
    POST — Receives real-time lead / messaging updates from Meta.
    """

    permission_classes = [AllowAny]
    authentication_classes = []  # No auth – Meta cannot authenticate with our JWT

    # ------------------------------------------------------------------ #
    #  GET – Webhook Verification
    # ------------------------------------------------------------------ #
    def get(self, request, *args, **kwargs):
        """
        Meta sends a GET request with the following query parameters
        when you first subscribe to a webhook:
          • hub.mode        — should be "subscribe"
          • hub.verify_token — the token you set in the Meta dashboard
          • hub.challenge   — an int Meta expects you to echo back
        """
        mode = request.query_params.get("hub.mode")
        token = request.query_params.get("hub.verify_token")
        challenge = request.query_params.get("hub.challenge")

        if mode == "subscribe" and token == VERIFY_TOKEN:
            logger.info("Meta webhook verified successfully.")
            return Response(int(challenge), status=status.HTTP_200_OK)

        logger.warning("Meta webhook verification failed. Token mismatch or invalid mode.")
        return Response({"error": "Verification failed"}, status=status.HTTP_403_FORBIDDEN)

    # ------------------------------------------------------------------ #
    #  POST – Receive Webhook Events
    # ------------------------------------------------------------------ #
    def post(self, request, *args, **kwargs):
        """
        Meta sends a POST request with a JSON payload whenever the
        subscribed event fires (e.g. new lead, message, etc.).

        Payload structure (leadgen example):
        {
            "object": "page",
            "entry": [
                {
                    "id": "<PAGE_ID>",
                    "time": 1234567890,
                    "changes": [
                        {
                            "field": "leadgen",
                            "value": {
                                "form_id": "...",
                                "leadgen_id": "...",
                                "page_id": "...",
                                "created_time": 1234567890,
                            }
                        }
                    ]
                }
            ]
        }
        """
        payload = request.data

        print("Meta webhook payload: ", payload, flush=True)

        if not payload:
            print("\n\n\nEmpty payload received from Meta webhook.", flush=True)
            return Response(
                {"error": "Empty payload"},
                status=status.HTTP_400_BAD_REQUEST,
            )

        obj_type = payload.get("object")
        print("Meta webhook event received — object: ", obj_type, flush=True)

        entries = payload.get("entry", [])
        for entry in entries:
            entry_id = entry.get("id")
            changes = entry.get("changes", [])
            messaging = entry.get("messaging", [])

            # ---------- Lead-gen / field-change events ---------- #
            for change in changes:
                field = change.get("field")
                value = change.get("value", {})
                
                if field == "leadgen":
                    leadgen_id = value.get("leadgen_id")
                    print("\n\n\nLeadgen ID: ", leadgen_id, flush=True)
                    leadgen_data = self._fetch_leadgen_data(leadgen_id)
                    print("\n\n\nLeadgen data: ", leadgen_data, flush=True)
                    
                    if leadgen_data:
                        field_data_list = leadgen_data.get("field_data", [])
                        custom_data = {}
                        full_name = ""
                        phone = ""
                        email = ""
                        job_title = ""
                        
                        for field_item in field_data_list:
                            name = field_item.get("name", "")
                            values_list = field_item.get("values", [])
                            val = values_list[0] if values_list else ""
                            
                            if name == "full_name":
                                full_name = val
                            elif name == "phone":
                                phone = val
                            elif name == "email":
                                email = val.lower() if val else ""
                            elif name == "job_title":
                                job_title = val
                            else:
                                custom_data[name] = val
                                
                        created_time_str = leadgen_data.get("created_time")
                        created_time = parse_datetime(created_time_str) if created_time_str else None
                        
                        try:
                            lead, created = Lead.objects.update_or_create(
                                leadgen_id=leadgen_data.get("id", leadgen_id),
                                defaults={
                                    "created_time": created_time,
                                    "full_name": full_name,
                                    "phone": phone,
                                    "email": email,
                                    "job_title": job_title,
                                    "custom_data": custom_data
                                }
                            )
                            
                            if created:
                                first_stage = LeadStage.objects.order_by('order').first()
                                if first_stage:
                                    lead.stage = first_stage
                                    lead.save(update_fields=['stage'])
                                    print(f"\n\n\nLead stage set to '{first_stage.name}'", flush=True)
                                    
                            print(f"\n\n\nLead saved: {lead.id} (Created: {created})", flush=True)
                        except Exception as e:
                            print(f"\n\n\nError saving lead: {e}", flush=True)

            # ---------- Messaging events (Messenger / IG) ------- #
            # for message in messaging:
            #     sender = message.get("sender", {}).get("id")
            #     print("Message — entry %s | sender: %s", entry_id, sender, flush=True)
            #     self._handle_message(entry_id, message)

        return Response({"status": "ok"}, status=status.HTTP_200_OK)

    # ------------------------------------------------------------------ #
    #  Private helpers – override / extend as your models evolve
    # ------------------------------------------------------------------ #
    def _handle_change(self, entry_id: str, field: str, value: dict):
        """Process a single field-change event (e.g. leadgen)."""
        # TODO: persist lead data, trigger notifications, etc.
        pass

    def _handle_message(self, entry_id: str, message: dict):
        """Process a single messaging event."""
        # TODO: persist message, trigger auto-replies, etc.
        pass

    def _fetch_leadgen_data(self, leadgen_id: str):
        """Fetch leadgen data from Meta."""
        url = f"https://graph.facebook.com/v19.0/{leadgen_id}"
        headers = {
            "Authorization": f"Bearer {settings.META_PAGE_ACCESS_TOKEN}",
            "fields": "id,created_time,field_data,form_id,ad_id"
        }
        response = requests.get(url, headers=headers)
        if response.status_code == 200:
            return response.json()
        else:
            return None
