# app/utils/email_sender.py | Created: 2026-09-25
import os
import smtplib
import ssl
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from email.mime.application import MIMEApplication


def send_invoice_email(
    to_email: str,
    customer_name: str,
    invoice_id: int,
    pdf_bytes: bytes,
    company_name: str = "BMS Autoglass",
) -> bool:
    """
    Envia el PDF del invoice por email usando Gmail SMTP.
    Requiere variables de entorno: SMTP_USER y SMTP_PASS.
    """
    smtp_user = os.getenv("SMTP_USER")
    smtp_pass = os.getenv("SMTP_PASS")
    smtp_host = os.getenv("SMTP_HOST", "smtp.gmail.com")
    smtp_port = int(os.getenv("SMTP_PORT", "587"))

    if not smtp_user or not smtp_pass:
        raise Exception("SMTP no configurado. Faltan SMTP_USER / SMTP_PASS.")

    if not to_email:
        raise Exception("No se especifico un email de destino.")

    subject = f"Invoice #{invoice_id} - {company_name}"

    body = f"""Hello {customer_name},

Please find attached your invoice #{invoice_id} from {company_name}.

If you have any questions, please reply to this email.

Thank you for your business.

Best regards,
{company_name}
"""

    msg = MIMEMultipart()
    msg["From"] = f"{company_name} <{smtp_user}>"
    msg["To"] = to_email
    msg["Subject"] = subject
    msg.attach(MIMEText(body, "plain"))

    # Adjuntar PDF
    part = MIMEApplication(pdf_bytes, _subtype="pdf")
    part.add_header(
        "Content-Disposition",
        f"attachment; filename=invoice_{invoice_id}.pdf",
    )
    msg.attach(part)

    context = ssl.create_default_context()
    with smtplib.SMTP(smtp_host, smtp_port) as server:
        server.starttls(context=context)
        server.login(smtp_user, smtp_pass)
        server.send_message(msg)

    return True