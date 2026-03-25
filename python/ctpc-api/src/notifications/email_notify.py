"""
Email notification system for CT scan events.

Sends HTML emails in German via SMTP. Gracefully degrades when SMTP
is not configured (logs a warning instead of crashing).

Environment variables:
  SMTP_HOST, SMTP_PORT, SMTP_USER, SMTP_PASS — SMTP server credentials
  NOTIFY_FROM — sender address (default: noreply@3dreamz.de)
  NOTIFY_TO   — recipient address(es), comma-separated
"""

from __future__ import annotations

import logging
import os
import smtplib
from datetime import datetime, timezone
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from ..queue.task_queue import QueueStats, ScanTask

logger = logging.getLogger(__name__)


class EmailNotifier:
    """Sends scan-related notification emails via SMTP."""

    def __init__(self) -> None:
        self.host = os.getenv("SMTP_HOST", "")
        self.port = int(os.getenv("SMTP_PORT", "587"))
        self.user = os.getenv("SMTP_USER", "")
        self.password = os.getenv("SMTP_PASS", "")
        self.from_addr = os.getenv("NOTIFY_FROM", "noreply@3dreamz.de")
        self.to_addrs = [
            a.strip() for a in os.getenv("NOTIFY_TO", "").split(",") if a.strip()
        ]

    @property
    def is_configured(self) -> bool:
        return bool(self.host and self.to_addrs)

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------

    def send_scan_complete(self, task: ScanTask) -> bool:
        """Send an HTML email when a scan completes successfully."""
        result_label = task.result or "—"
        result_color = "#27ae60" if task.result == "IO" else "#e74c3c"
        stl_info = f"<p><strong>STL-Datei:</strong> {task.stl_path}</p>" if task.stl_path else ""

        duration = self._format_duration(task.started_at, task.completed_at)

        subject = f"Scan abgeschlossen: {task.part_name} — {result_label}"
        html = f"""\
<!DOCTYPE html>
<html lang="de">
<head><meta charset="utf-8"></head>
<body style="font-family: Arial, sans-serif; background: #f4f4f4; padding: 20px;">
  <div style="max-width: 600px; margin: auto; background: #fff; border-radius: 8px; overflow: hidden; box-shadow: 0 2px 8px rgba(0,0,0,0.1);">
    <div style="background: {result_color}; color: #fff; padding: 20px 24px;">
      <h1 style="margin: 0; font-size: 22px;">Scan abgeschlossen</h1>
    </div>
    <div style="padding: 24px;">
      <table style="width: 100%; border-collapse: collapse;">
        <tr><td style="padding: 8px 0; color: #666;">Bauteil:</td><td style="padding: 8px 0;"><strong>{task.part_name}</strong></td></tr>
        <tr><td style="padding: 8px 0; color: #666;">Profil:</td><td style="padding: 8px 0;">{task.profile_name}</td></tr>
        <tr><td style="padding: 8px 0; color: #666;">Ergebnis:</td><td style="padding: 8px 0;"><span style="background: {result_color}; color: #fff; padding: 4px 12px; border-radius: 4px; font-weight: bold;">{result_label}</span></td></tr>
        <tr><td style="padding: 8px 0; color: #666;">Dauer:</td><td style="padding: 8px 0;">{duration}</td></tr>
        <tr><td style="padding: 8px 0; color: #666;">Abgeschlossen:</td><td style="padding: 8px 0;">{self._format_timestamp(task.completed_at)}</td></tr>
      </table>
      {stl_info}
    </div>
    <div style="background: #f9f9f9; padding: 12px 24px; font-size: 12px; color: #999;">
      CT-PC AutoPilot &mdash; Automatische Benachrichtigung
    </div>
  </div>
</body>
</html>"""

        return self._send(subject, html)

    def send_scan_failed(self, task: ScanTask) -> bool:
        """Send an HTML email when a scan fails."""
        error_text = task.error_message or "Unbekannter Fehler"
        duration = self._format_duration(task.started_at, task.completed_at)

        subject = f"Scan fehlgeschlagen: {task.part_name}"
        html = f"""\
<!DOCTYPE html>
<html lang="de">
<head><meta charset="utf-8"></head>
<body style="font-family: Arial, sans-serif; background: #f4f4f4; padding: 20px;">
  <div style="max-width: 600px; margin: auto; background: #fff; border-radius: 8px; overflow: hidden; box-shadow: 0 2px 8px rgba(0,0,0,0.1);">
    <div style="background: #e74c3c; color: #fff; padding: 20px 24px;">
      <h1 style="margin: 0; font-size: 22px;">Scan fehlgeschlagen</h1>
    </div>
    <div style="padding: 24px;">
      <table style="width: 100%; border-collapse: collapse;">
        <tr><td style="padding: 8px 0; color: #666;">Bauteil:</td><td style="padding: 8px 0;"><strong>{task.part_name}</strong></td></tr>
        <tr><td style="padding: 8px 0; color: #666;">Profil:</td><td style="padding: 8px 0;">{task.profile_name}</td></tr>
        <tr><td style="padding: 8px 0; color: #666;">Dauer:</td><td style="padding: 8px 0;">{duration}</td></tr>
      </table>
      <div style="margin-top: 16px; padding: 16px; background: #fdf0ef; border-left: 4px solid #e74c3c; border-radius: 4px;">
        <strong>Fehler:</strong><br>
        <code style="font-size: 13px;">{error_text}</code>
      </div>
      <p style="margin-top: 16px; color: #666; font-size: 13px;">
        Bitte den Scan-Vorgang und die Maschine pruefen. Der Auftrag kann ueber die Queue erneut gestartet werden.
      </p>
    </div>
    <div style="background: #f9f9f9; padding: 12px 24px; font-size: 12px; color: #999;">
      CT-PC AutoPilot &mdash; Automatische Benachrichtigung
    </div>
  </div>
</body>
</html>"""

        return self._send(subject, html)

    def send_daily_summary(self, stats: QueueStats) -> bool:
        """Send a daily digest of queue statistics."""
        today = datetime.now(timezone.utc).strftime("%d.%m.%Y")
        avg_min = stats.avg_duration_s / 60 if stats.avg_duration_s else 0

        subject = f"Tagesbericht CT-Scans — {today}"
        html = f"""\
<!DOCTYPE html>
<html lang="de">
<head><meta charset="utf-8"></head>
<body style="font-family: Arial, sans-serif; background: #f4f4f4; padding: 20px;">
  <div style="max-width: 600px; margin: auto; background: #fff; border-radius: 8px; overflow: hidden; box-shadow: 0 2px 8px rgba(0,0,0,0.1);">
    <div style="background: #2c3e50; color: #fff; padding: 20px 24px;">
      <h1 style="margin: 0; font-size: 22px;">Tagesbericht CT-Scans</h1>
      <p style="margin: 4px 0 0; opacity: 0.8;">{today}</p>
    </div>
    <div style="padding: 24px;">
      <table style="width: 100%; border-collapse: collapse;">
        <tr style="border-bottom: 1px solid #eee;">
          <td style="padding: 12px 0; color: #666;">Gesamt Auftraege:</td>
          <td style="padding: 12px 0; font-size: 20px; font-weight: bold;">{stats.total}</td>
        </tr>
        <tr style="border-bottom: 1px solid #eee;">
          <td style="padding: 12px 0; color: #666;">In Warteschlange:</td>
          <td style="padding: 12px 0;">{stats.queued}</td>
        </tr>
        <tr style="border-bottom: 1px solid #eee;">
          <td style="padding: 12px 0; color: #666;">Aktiv:</td>
          <td style="padding: 12px 0;">{stats.active}</td>
        </tr>
        <tr style="border-bottom: 1px solid #eee;">
          <td style="padding: 12px 0; color: #666;">Abgeschlossen:</td>
          <td style="padding: 12px 0; color: #27ae60; font-weight: bold;">{stats.completed}</td>
        </tr>
        <tr style="border-bottom: 1px solid #eee;">
          <td style="padding: 12px 0; color: #666;">Fehlgeschlagen:</td>
          <td style="padding: 12px 0; color: #e74c3c; font-weight: bold;">{stats.failed}</td>
        </tr>
        <tr style="border-bottom: 1px solid #eee;">
          <td style="padding: 12px 0; color: #666;">Abgebrochen:</td>
          <td style="padding: 12px 0;">{stats.cancelled}</td>
        </tr>
        <tr>
          <td style="padding: 12px 0; color: #666;">Durchschn. Dauer:</td>
          <td style="padding: 12px 0;">{avg_min:.1f} Minuten</td>
        </tr>
      </table>
    </div>
    <div style="background: #f9f9f9; padding: 12px 24px; font-size: 12px; color: #999;">
      CT-PC AutoPilot &mdash; Automatische Benachrichtigung
    </div>
  </div>
</body>
</html>"""

        return self._send(subject, html)

    # ------------------------------------------------------------------
    # Internals
    # ------------------------------------------------------------------

    def _send(self, subject: str, html_body: str) -> bool:
        """Send an HTML email. Returns True on success, False on failure."""
        if not self.is_configured:
            logger.warning(
                "Email not configured (SMTP_HOST=%s, NOTIFY_TO=%s) — skipping: %s",
                self.host or "<empty>",
                ",".join(self.to_addrs) or "<empty>",
                subject,
            )
            return False

        try:
            msg = MIMEMultipart("alternative")
            msg["Subject"] = subject
            msg["From"] = self.from_addr
            msg["To"] = ", ".join(self.to_addrs)
            msg.attach(MIMEText(html_body, "html", "utf-8"))

            with smtplib.SMTP(self.host, self.port, timeout=15) as server:
                server.ehlo()
                if self.port != 25:
                    server.starttls()
                    server.ehlo()
                if self.user and self.password:
                    server.login(self.user, self.password)
                server.sendmail(self.from_addr, self.to_addrs, msg.as_string())

            logger.info("Email sent: %s -> %s", subject, ", ".join(self.to_addrs))
            return True

        except Exception as exc:
            logger.warning("Failed to send email '%s': %s", subject, exc)
            return False

    @staticmethod
    def _format_duration(started_at: str | None, completed_at: str | None) -> str:
        """Format the duration between two ISO timestamps as human-readable German string."""
        if not started_at or not completed_at:
            return "—"
        try:
            start = datetime.fromisoformat(started_at)
            end = datetime.fromisoformat(completed_at)
            delta = (end - start).total_seconds()
            if delta < 60:
                return f"{delta:.0f} Sekunden"
            elif delta < 3600:
                return f"{delta / 60:.1f} Minuten"
            else:
                return f"{delta / 3600:.1f} Stunden"
        except (ValueError, TypeError):
            return "—"

    @staticmethod
    def _format_timestamp(iso_str: str | None) -> str:
        """Format an ISO timestamp to German date/time string."""
        if not iso_str:
            return "—"
        try:
            dt = datetime.fromisoformat(iso_str)
            return dt.strftime("%d.%m.%Y %H:%M Uhr")
        except (ValueError, TypeError):
            return iso_str or "—"
