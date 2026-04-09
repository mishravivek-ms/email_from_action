import logging
import os
from typing import Optional

from azure.communication.email import EmailClient
from azure.core.exceptions import ServiceRequestError
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel, EmailStr

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("email-api")

app = FastAPI(title="Email API", version="1.0.0")


class EmailRequest(BaseModel):
    to: Optional[EmailStr] = None
    subject: Optional[str] = None
    plainText: Optional[str] = None
    html: Optional[str] = None


def _get_setting(name: str) -> Optional[str]:
    return os.getenv(name)


@app.get("/health")
def health() -> dict:
    return {"status": "ok"}


@app.post("/email")
def send_email(payload: EmailRequest) -> dict:

    connection_string = _get_setting("ACS_EMAIL_CONNECTION_STRING")
    sender_address = _get_setting("ACS_EMAIL_SENDER")
    default_recipient = _get_setting("ACS_EMAIL_DEFAULT_TO")

    if not connection_string or not sender_address or not default_recipient:
        raise HTTPException(
            status_code=500,
            detail=(
                "Missing required settings: ACS_EMAIL_CONNECTION_STRING, "
                "ACS_EMAIL_SENDER, ACS_EMAIL_DEFAULT_TO."
            ),
        )

    recipient = payload.to or default_recipient
    subject = payload.subject or "Azure App Service Email Test"
    plain_text = payload.plainText or "Hello from Azure App Service API."
    html_body = payload.html or f"<html><body><h1>{plain_text}</h1></body></html>"

    try:
        client = EmailClient.from_connection_string(connection_string)
        message = {
            "senderAddress": sender_address,
            "recipients": {"to": [{"address": recipient}]},
            "content": {
                "subject": subject,
                "plainText": plain_text,
                "html": html_body,
            },
        }

        poller = client.begin_send(message)
        result = poller.result()
        message_id = getattr(result, "message_id", None)
        if message_id is None and isinstance(result, dict):
            message_id = result.get("messageId") or result.get("message_id")

        return {"status": "sent", "messageId": message_id}
    except ServiceRequestError as ex:
        raise HTTPException(status_code=502, detail=f"Email service connection error: {ex}")
    except Exception as ex:
        text = str(ex)
        if "DomainNotLinked" in text:
            raise HTTPException(
                status_code=400,
                detail=(
                    "Sender domain is not linked to this Communication Service. "
                    "Use the correct sender or connection string."
                ),
            )
        raise HTTPException(status_code=500, detail=f"Failed to send email: {text}")
