import os
import hashlib
from mailchimp_marketing import Client
from mailchimp_marketing.api_client import ApiClientError

MAILCHIMP_API_KEY = os.getenv("MAILCHIMP_API_KEY")
MAILCHIMP_SERVER_PREFIX = os.getenv("MAILCHIMP_SERVER_PREFIX")
MAILCHIMP_AUDIENCE_ID = os.getenv("MAILCHIMP_AUDIENCE_ID")

def get_mailchimp_client():
    client = Client()
    client.set_config({
        "api_key": MAILCHIMP_API_KEY,
        "server": MAILCHIMP_SERVER_PREFIX
    })
    return client

def _subscriber_hash(email: str) -> str:
    return hashlib.md5((email or '').strip().lower().encode('utf-8')).hexdigest()


def add_lead_to_mailchimp(email, first_name="", last_name="", tag_names=None):
    client = get_mailchimp_client()
    try:
        email = (email or '').strip()
        if not email:
            return {"error": "Email is required"}

        subscriber_hash = _subscriber_hash(email)

        # Upsert member (avoids failing when member already exists)
        response = client.lists.set_list_member(
            MAILCHIMP_AUDIENCE_ID,
            subscriber_hash,
            {
                "email_address": email,
                "status_if_new": "subscribed",
                "merge_fields": {
                    "FNAME": first_name or "",
                    "LNAME": last_name or "",
                },
            },
        )

        if tag_names:
            tags_payload = []
            for t in tag_names:
                if not t:
                    continue
                t = str(t).strip()
                if not t:
                    continue
                tags_payload.append({"name": t, "status": "active"})

            if tags_payload:
                client.lists.update_list_member_tags(
                    MAILCHIMP_AUDIENCE_ID,
                    subscriber_hash,
                    {"tags": tags_payload},
                )

        return response
    except ApiClientError as error:
        return {"error": str(error)}
