import os
import smtplib
from email.mime.text import MIMEText

EMAIL_TEMPLATES = {
    "review.request": {
        "subject": "Review requested: {stage} for idea #{idea_id}",
        "body": "A {stage} review has been requested for idea #{idea_id}.",
    },
    "review.sla_overdue": {
        "subject": "SLA overdue: {stage} review for idea #{idea_id}",
        "body": "Review #{review_id} (stage: {stage}) for idea #{idea_id} is overdue.",
    },
    "assignment.invite": {
        "subject": "Invitation: Idea #{idea_id}",
        "body": "You have been invited to take idea #{idea_id}. Please respond.",
    },
    "assignment.escalated": {
        "subject": "Assignment escalated: Idea #{idea_id}",
        "body": "Assignment #{assignment_id} for idea #{idea_id} has been escalated to admin/marketplace.",
    },
}


def get_smtp_config():
    return {
        "host": os.getenv("SMTP_HOST"),
        "port": int(os.getenv("SMTP_PORT", "0") or 0),
        "user": os.getenv("SMTP_USER"),
        "password": os.getenv("SMTP_PASSWORD"),
        "use_tls": os.getenv("SMTP_USE_TLS", "true").lower() in ("1", "true", "yes"),
        "from_email": os.getenv("SMTP_FROM", os.getenv("SMTP_USER", "no-reply@example.com")),
    }


def send_email_smtp(to_email: str, subject: str, body: str) -> str:
    cfg = get_smtp_config()
    if not cfg["host"] or not cfg["port"]:
        # No SMTP configured; simulate send for dev
        return "mock_sent"

    msg = MIMEText(body, "plain", "utf-8")
    msg["Subject"] = subject
    msg["From"] = cfg["from_email"]
    msg["To"] = to_email

    try:
        if cfg["use_tls"]:
            server = smtplib.SMTP(cfg["host"], cfg["port"])
            server.starttls()
        else:
            server = smtplib.SMTP(cfg["host"], cfg["port"])
        if cfg["user"] and cfg["password"]:
            server.login(cfg["user"], cfg["password"])
        server.send_message(msg)
        server.quit()
        return "sent"
    except Exception as e:
        return f"error:{e.__class__.__name__}"


def send_email(to_email: str, subject: str, body: str) -> str:
    provider = os.getenv("EMAIL_PROVIDER", "smtp").lower().strip()
    if provider == "mock":
        return "mock_sent"
    return send_email_smtp(to_email, subject, body)


def render_template(key: str, **context) -> tuple[str, str]:
    tpl = EMAIL_TEMPLATES.get(key)
    if not tpl:
        subject = key
        body = str(context)
        return subject, body
    return tpl["subject"].format(**context), tpl["body"].format(**context)


def is_retryable(status: str) -> bool:
    return status.lower() in {"error", "failed", "mock_sent"}
