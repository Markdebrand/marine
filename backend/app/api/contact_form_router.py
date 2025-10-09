from fastapi import APIRouter, HTTPException, status, Request
from pydantic import BaseModel, EmailStr
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
import os

router = APIRouter()

class ContactForm(BaseModel):
    name: str
    phone: str
    email: EmailStr
    company: str
    subject: str
    question: str

@router.post("/contact-us", status_code=status.HTTP_200_OK)
def contact_us(form: ContactForm, request: Request):
    # Use centralized settings where possible
    from app.config import settings as cfg

    smtp_host = cfg.SMTP_HOST
    smtp_port = int(os.getenv("SMTP_PORT", str(cfg.SMTP_PORT or 587)))
    smtp_user = cfg.SMTP_USER
    smtp_password = cfg.SMTP_PASSWORD
    smtp_sender = cfg.EMAIL_SENDER

    # Build recipient list: CONTACT_FORM_TO (priority) else EMAIL_TO
    recipients: list[str] = []
    cf_to = getattr(cfg, "CONTACT_FORM_TO", []) or []
    if isinstance(cf_to, (list, tuple)) and cf_to:
        recipients = list(cf_to)
    elif getattr(cfg, "EMAIL_TO", None):
        recipients = list(getattr(cfg, "EMAIL_TO") or [])

    # Fallback to support address if nothing configured
    smtp_to_list = recipients if recipients else ["support@hsomarine.com"]
    smtp_tls = cfg.SMTP_TLS if hasattr(cfg, "SMTP_TLS") else os.getenv("SMTP_TLS", "true").lower() == "true"

    # Validar que las variables SMTP estén definidas mínimamente
    if not all([smtp_host, smtp_user, smtp_password, smtp_sender]):
        raise HTTPException(status_code=500, detail="Faltan variables de configuración SMTP en el servidor.")

    subject = f"Nuevo mensaje de Contact Us: {form.subject}"
    body = (
        f"Nombre: {form.name}\n"
        f"Teléfono: {form.phone}\n"
        f"Email: {form.email}\n"
        f"Empresa: {form.company}\n"
        f"Asunto: {form.subject}\n"
        f"Pregunta: {form.question}"
    )

    msg = MIMEMultipart()
    msg["From"] = str(smtp_sender)
    msg["To"] = ",".join(smtp_to_list)
    # msg["Cc"] = str(smtp_cc)
    msg["Subject"] = subject
    msg.attach(MIMEText(body, "plain"))

    try:
        server = smtplib.SMTP(str(smtp_host), smtp_port)
        if smtp_tls:
            server.starttls()
        server.login(str(smtp_user), str(smtp_password))
        # Enviar a destinatario(s)
        to_addrs = [x.strip() for x in smtp_to_list if x and x.strip()]
        server.sendmail(str(smtp_sender), to_addrs, msg.as_string())
        server.quit()
        return {"detail": "Mensaje enviado correctamente", "to": to_addrs}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error al enviar el correo: {str(e)}")
