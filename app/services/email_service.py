import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
import requests
from app.config import settings


def send_signup_verification_link(to_email: str, token: str):
    verification_link = f"{settings.FRONTEND_URL}/verify-email?token={token}"
    _send_via_brevo(
        to_email=to_email,
        subject="تأكيد إنشاء الحساب - غصن",
        html_content=f"""
            <p>مرحباً،</p>
            <p>اضغطي على الرابط التالي لتأكيد إنشاء حسابك على منصة غصن:</p>
            <p><a href="{verification_link}">{verification_link}</a></p>
            <p>هذا الرابط صالح لمدة 10 دقائق.</p>
        """,
    )


def send_password_reset_link(to_email: str, token: str):
    reset_link = f"{settings.FRONTEND_URL}/reset-password?token={token}"
    _send_via_brevo(
        to_email=to_email,
        subject="استرداد كلمة السر - غصن",
        html_content=f"""
            <p>مرحباً،</p>
            <p>اضغطي على الرابط التالي لإعادة تعيين كلمة السر (صالح لمدة 10 دقائق):</p>
            <p><a href="{reset_link}">{reset_link}</a></p>
            <p>إذا لم تطلبي هذا، تجاهلي هذا البريد.</p>
        """,
    )


def _send_via_brevo(to_email: str, subject: str, html_content: str):
    headers = {
        "accept": "application/json",
        "api-key": settings.BREVO_API_KEY,
        "content-type": "application/json",
    }

    payload = {
        "sender": {
            "name": settings.BREVO_SENDER_NAME,
            "email": settings.BREVO_SENDER_EMAIL
        },
        "to": [
            {"email": to_email}
        ],
        "subject": subject,
        "htmlContent": html_content,
    }

    response = requests.post(
        "https://api.brevo.com/v3/smtp/email",
        json=payload,
        headers=headers,
        timeout=15
    )

    print("Brevo status:", response.status_code, flush=True)
    print("Brevo response:", response.text, flush=True)

    response.raise_for_status()
    