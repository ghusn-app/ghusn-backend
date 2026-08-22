import os
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from dotenv import load_dotenv

load_dotenv()

SMTP_SERVER = os.getenv("SMTP_SERVER")
SMTP_PORT = int(os.getenv("SMTP_PORT"))
SMTP_EMAIL = os.getenv("SMTP_EMAIL")
SMTP_PASSWORD = os.getenv("SMTP_PASSWORD")


def send_password_reset_code(to_email: str, code: str):
    message = MIMEMultipart()
    message["From"] = SMTP_EMAIL
    message["To"] = to_email
    message["Subject"] = "رمز استرداد كلمة السر - غصن"

    body = f"""
    مرحباً،

    رمز التحقق لاسترداد كلمة السر الخاصة بحسابك على منصة غصن هو:

    {code}

    هذا الرمز صالح لمدة 10 دقائق. إذا لم تطلب هذا، تجاهل هذا البريد.
    """
    message.attach(MIMEText(body, "plain"))

    with smtplib.SMTP(SMTP_SERVER, SMTP_PORT) as server:
        server.starttls()
        server.login(SMTP_EMAIL, SMTP_PASSWORD)
        server.send_message(message)