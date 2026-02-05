import logging

from app.config import settings

logger = logging.getLogger(__name__)


def send_prospect_email(email: str, first_name: str) -> None:
    """Send confirmation email to the prospect who submitted a lead.

    In production, replace with actual SMTP / SendGrid / SES integration.
    """
    logger.info(
        "Sending prospect confirmation email to %s (name: %s)",
        email,
        first_name,
    )


def send_attorney_email(lead_id: str, first_name: str, last_name: str) -> None:
    """Notify the attorney that a new lead has been submitted.

    In production, replace with actual SMTP / SendGrid / SES integration.
    """
    logger.info(
        "Notifying attorney at %s about new lead %s: %s %s",
        settings.ATTORNEY_EMAIL,
        lead_id,
        first_name,
        last_name,
    )
