"""
Notification service — Email via SendGrid, SMS via Twilio.
Both channels are no-ops when their respective env vars are not configured.
"""
import logging
from dataclasses import dataclass

from app.core.config import settings

logger = logging.getLogger(__name__)


@dataclass
class AlertPayload:
    disease:      str
    risk_level:   str
    expected_cases: int
    location_name: str | None
    lat:          float
    lon:          float
    recommended_action: str


async def send_email_alert(to_email: str, payload: AlertPayload) -> bool:
    """Send a high-risk outbreak email via SendGrid. Returns True on success."""
    if not settings.SENDGRID_API_KEY:
        logger.debug("SENDGRID_API_KEY not set — email alert skipped")
        return False

    try:
        import httpx

        subject = f"[ClimateHealth AI] High {payload.disease.title()} Risk — {payload.location_name or f'{payload.lat},{payload.lon}'}"
        body = (
            f"HIGH RISK ALERT\n\n"
            f"Disease:         {payload.disease.title()}\n"
            f"Location:        {payload.location_name or f'({payload.lat}, {payload.lon})'}\n"
            f"Expected Cases:  {payload.expected_cases}\n"
            f"Risk Level:      {payload.risk_level}\n\n"
            f"Recommended Action:\n{payload.recommended_action}\n\n"
            f"— ClimateHealth AI"
        )

        async with httpx.AsyncClient(timeout=10) as client:
            resp = await client.post(
                "https://api.sendgrid.com/v3/mail/send",
                headers={
                    "Authorization": f"Bearer {settings.SENDGRID_API_KEY}",
                    "Content-Type":  "application/json",
                },
                json={
                    "personalizations": [{"to": [{"email": to_email}]}],
                    "from":    {"email": settings.ALERT_FROM_EMAIL},
                    "subject": subject,
                    "content": [{"type": "text/plain", "value": body}],
                },
            )
            resp.raise_for_status()
        logger.info("Email alert sent to %s for %s", to_email, payload.disease)
        return True
    except Exception as e:
        logger.error("Email alert failed: %s", e)
        return False


async def send_sms_alert(to_phone: str, payload: AlertPayload) -> bool:
    """Send a high-risk outbreak SMS via Twilio. Returns True on success."""
    if not (settings.TWILIO_ACCOUNT_SID and settings.TWILIO_AUTH_TOKEN and settings.TWILIO_FROM_NUMBER):
        logger.debug("Twilio credentials not set — SMS alert skipped")
        return False

    try:
        import httpx
        from base64 import b64encode

        location = payload.location_name or f"({payload.lat:.2f}, {payload.lon:.2f})"
        message  = (
            f"[ClimateHealth AI] HIGH {payload.disease.upper()} RISK at {location}. "
            f"Expected cases: {payload.expected_cases}. "
            f"Action: {payload.recommended_action[:100]}"
        )

        auth = b64encode(f"{settings.TWILIO_ACCOUNT_SID}:{settings.TWILIO_AUTH_TOKEN}".encode()).decode()
        url  = f"https://api.twilio.com/2010-04-01/Accounts/{settings.TWILIO_ACCOUNT_SID}/Messages.json"

        async with httpx.AsyncClient(timeout=10) as client:
            resp = await client.post(
                url,
                headers={"Authorization": f"Basic {auth}"},
                data={"From": settings.TWILIO_FROM_NUMBER, "To": to_phone, "Body": message},
            )
            resp.raise_for_status()
        logger.info("SMS alert sent to %s for %s", to_phone, payload.disease)
        return True
    except Exception as e:
        logger.error("SMS alert failed: %s", e)
        return False
