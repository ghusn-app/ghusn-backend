import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from app.config import settings


def send_password_reset_link(to_email: str, token: str):
    reset_link = f"{settings.FRONTEND_URL}/reset-password?token={token}"

    message = MIMEMultipart()
    message["From"] = settings.SMTP_EMAIL
    message["To"] = to_email
    message["Subject"] = "استرداد كلمة السر - غصن"

    body = f"""
    مرحباً،

    اضغطي على الرابط التالي لإعادة تعيين كلمة السر (صالح لمدة 10 دقائق):

    {reset_link}

    إذا لم تطلبي هذا، تجاهلي هذا البريد.
    """
    message.attach(MIMEText(body, "plain"))

    with smtplib.SMTP(settings.SMTP_SERVER, settings.SMTP_PORT) as server:
        server.starttls()
        server.login(settings.SMTP_EMAIL, settings.SMTP_PASSWORD)
        server.send_message(message)


def send_signup_verification_link(to_email: str, token: str):
    verification_link = f"{settings.FRONTEND_URL}/verify-email?token={token}"

    message = MIMEMultipart()
    message["From"] = settings.SMTP_EMAIL
    message["To"] = to_email
    message["Subject"] = "تأكيد إنشاء الحساب - غصن"

    body = f"""
    مرحباً،

    اضغطي على الرابط التالي لتأكيد إنشاء حسابك على منصة غصن:

    {verification_link}

    هذا الرابط صالح لمدة 10 دقائق.
    """
    message.attach(MIMEText(body, "plain"))

    with smtplib.SMTP(settings.SMTP_SERVER, settings.SMTP_PORT) as server:
        server.starttls()
        server.login(settings.SMTP_EMAIL, settings.SMTP_PASSWORD)
        server.send_message(message)