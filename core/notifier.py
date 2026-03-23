import smtplib
import logging
import asyncio
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from pathlib import Path
from .config import config

class Notifier:
    def __init__(self):
        self.template_path = Path(__file__).parent / "templates" / "email_template.html"

    def _render_template(self, **kwargs) -> str:
        if not self.template_path.exists():
            return f"<h1>{kwargs.get('title', 'Notification')}</h1><p>{kwargs.get('description', '')}</p>"
        
        template = self.template_path.read_text()
        
        # Simple placeholder replacement
        for key, value in kwargs.items():
            if key == "details" and isinstance(value, dict):
                details_html = "".join([f'<tr><td class="label">{k}</td><td class="value">{v}</td></tr>' for k, v in value.items()])
                # Remove loop tags and inject html
                template = template.replace("{% if details %}", "").replace("{% endif %}", "")
                template = template.replace("{% for key, value in details.items() %}", "").replace("{% endfor %}", "")
                template = template.replace('<td class="label">{{ key }}</td>', "").replace('<td class="value">{{ value }}</td>', details_html)
            else:
                template = template.replace(f"{{{{ {key} }}}}", str(value))
        
        # Cleanup
        return template.replace("{% if details %}", "").replace("{% endif %}", "")

    async def send_notification(self, title: str, description: str, status: str = "success", details: dict | None = None):
        """Unified method for all notifications."""
        await self.send_email(title, description, status, details)

    async def send_email(self, title: str, description: str, status: str = "success", details: dict | None = None):
        if config.get("NOTIFY_EMAIL", "False").lower() != "true":
            return

        email_addr = config.get("EMAIL")
        password = config.get("EMAIL_PASSWORD")
        
        if not email_addr or not password:
            logging.error("Email notifications enabled but credentials missing.")
            return

        body = self._render_template(
            title=title,
            description=description,
            status_class="status-success" if status == "success" else "status-error",
            status_text="Success" if status == "success" else "Action Required",
            details=details or {}
        )

        message = MIMEMultipart()
        message["Subject"] = f"OracleFT: {title}"
        message["From"] = f"OracleFT <{email_addr}>"
        message["To"] = email_addr
        message.attach(MIMEText(body, "html"))

        def _send():
            with smtplib.SMTP("smtp.gmail.com", 587) as server:
                server.starttls()
                server.login(email_addr, password)
                server.sendmail(email_addr, email_addr, message.as_string())

        try:
            await asyncio.to_thread(_send)
            logging.info("Email notification sent: %s", title)
        except Exception as e:
            logging.error("Failed to send email: %s", e)

notifier = Notifier()
