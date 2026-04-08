import logging
import os
import re

import azure.functions as func
from azure.communication.email import EmailClient

# Simple RFC-5321-inspired pattern for basic email address validation
_EMAIL_RE = re.compile(r"^[^@\s]+@[^@\s]+\.[^@\s]+$")


def _is_valid_email(address: str) -> bool:
    return bool(_EMAIL_RE.match(address))


def main(req: func.HttpRequest) -> func.HttpResponse:
    """HTTP-triggered Azure Function that sends an email via Azure Communication Services."""
    logging.info("SendEmail function triggered.")

    # Read configuration from environment variables (set in local.settings.json or App Settings)
    connection_string = os.environ.get("COMMUNICATION_SERVICES_CONNECTION_STRING", "")
    sender_address = os.environ.get("SENDER_ADDRESS", "")
    recipient_address = os.environ.get("RECIPIENT_ADDRESS", "")

    # Allow the caller to override the recipient via query string or JSON body
    recipient_override = req.params.get("recipient")
    if not recipient_override:
        try:
            body = req.get_json()
            recipient_override = body.get("recipient")
        except ValueError:
            pass

    if recipient_override:
        if not _is_valid_email(recipient_override):
            return func.HttpResponse(
                "Invalid recipient email address.",
                status_code=400,
            )
        recipient_address = recipient_override

    if not connection_string:
        return func.HttpResponse(
            "COMMUNICATION_SERVICES_CONNECTION_STRING is not configured.",
            status_code=500,
        )

    if not sender_address or not recipient_address:
        return func.HttpResponse(
            "SENDER_ADDRESS and RECIPIENT_ADDRESS must be configured.",
            status_code=500,
        )

    try:
        client = EmailClient.from_connection_string(connection_string)

        message = {
            "senderAddress": sender_address,
            "recipients": {
                "to": [{"address": recipient_address}]
            },
            "content": {
                "subject": "Test Email!!!",
                "plainText": "Hello world via email.!!!!!",
                "html": """
                <html>
                    <body>
                        <h1>Hello world via email.!!!!!</h1>
                    </body>
                </html>
                """,
            },
        }

        poller = client.begin_send(message)
        result = poller.result()

        logging.info("Message sent: %s", result.message_id)
        return func.HttpResponse(
            f"Email sent successfully. Message ID: {result.message_id}",
            status_code=200,
        )

    except Exception as ex:
        logging.error("Failed to send email: %s", ex)
        return func.HttpResponse(
            "An error occurred while sending the email. Please check the function logs for details.",
            status_code=500,
        )
