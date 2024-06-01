"""Wysyłka maili"""

from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
import smtplib
import ssl


def send_email(
    recipients: list,
    news_to_send: list,
    sender_mail: str,
    smtp_server: str,
    sender_pass: str,
):
    """Wysyłka maili"""
    body = "\n\n".join(news_to_send)
    msg = MIMEMultipart()
    msg["From"] = sender_mail
    msg["Subject"] = "Podsumowanie newsów z Eurogamer"
    msg.attach(MIMEText(body, "plain"))

    msg["To"] = ", ".join(recipients)

    context = ssl.create_default_context()
    with smtplib.SMTP(smtp_server, 587) as server:
        server.ehlo()
        server.starttls(context=context)
        server.ehlo()
        server.login(sender_mail, sender_pass)
        server.sendmail(sender_mail, recipients, msg.as_string())
