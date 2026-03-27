#!/usr/bin/env python3
# -*- coding: utf-8 -*-
#ikut cjsd zhsx ulna 
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart

def send_html_mail(receiver_email: str, code: str):
    """
    Sendet eine HTML-E-Mail mit IES-Scan-Benachrichtigung.

    Parameter:
        receiver_email (str): Empfängeradresse
        code (str): HTML-Code der Nachricht (komplette E-Mail)
    """

    # Absenderdaten – bitte anpassen
    sender_email = "jonnyjonson2000@gmail.com"
    sender_name = "3Dreamz AutoPilot"
    smtp_server = "smtp.gmail.com"
    smtp_port = 587
    smtp_user = "jonnyjonson2000@gmail.com"
    smtp_password = "ikutcjsdzhsxulna"

    # E-Mail vorbereiten
    msg = MIMEMultipart("alternative")
    msg["Subject"] = "Ihr Scan ist fertiggestellt"
    msg["From"] = f"{sender_name} <{sender_email}>"
    msg["To"] = receiver_email

    # Text-Alternative (falls HTML nicht unterstützt wird)
    text_fallback = (
        "Ihr Scan wurde abgeschlossen.\n\n"
        "Bitte öffnen Sie den untenstehenden Link im Browser:\n"
        "(Dieser Link funktioniert nur innerhalb des IES-Netzwerks.)"
    )

    # MIME-Parts
    part_text = MIMEText(text_fallback, "plain", "utf-8")
    part_html = MIMEText(code, "html", "utf-8")

    msg.attach(part_text)
    msg.attach(part_html)

    # Verbindung & Versand
    try:
        with smtplib.SMTP(smtp_server, smtp_port) as server:
            server.starttls()  # für STARTTLS, entfernen falls nicht benötigt
            server.login(smtp_user, smtp_password)
            server.sendmail(sender_email, receiver_email, msg.as_string())
            print(f"[✔] E-Mail erfolgreich gesendet an {receiver_email}")
    except Exception as e:
        print(f"[x] Fehler beim Senden an {receiver_email}: {e}")

