from email_notify import send_html_mail
from render_email import render_email 

def notify_scan_completion(receiver_email: str, scan_id: str):
    """
    Renders the email for the given scan_id and sends it to the receiver_email.
    """
    try:
        html_code = render_email(scan_id)
        send_html_mail(receiver_email, html_code)
    except Exception as e:
        print(f"[x] Fehler beim Benachrichtigen des Scans {scan_id} an {receiver_email}: {e}")


notify_scan_completion("jonas.weber.1000@gmail.com", "abdc3")