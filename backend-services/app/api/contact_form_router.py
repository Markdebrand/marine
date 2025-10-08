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
    smtp_host = os.getenv("SMTP_HOST")
    smtp_port = int(os.getenv("SMTP_PORT", "587"))
    smtp_user = os.getenv("SMTP_USER")
    smtp_password = os.getenv("SMTP_PASSWORD")
    smtp_sender = os.getenv("EMAIL_SENDER")
    # Destinatarios configurables desde settings
    from app.config import settings as cfg
    # Compatibilidad: usa CONTACT_FORM_TO si existe, sino EMAIL_TO
    cf_to = getattr(cfg, "CONTACT_FORM_TO", None)
    recipients = []
    if isinstance(cf_to, (list, tuple)) and cf_to:
        recipients = list(cf_to)
    elif getattr(cfg, "EMAIL_TO", None):
        recipients = list(getattr(cfg, "EMAIL_TO"))
    # Fallback: soporte genérico si nada configurado
    smtp_to = ",".join(recipients) if recipients else "support@hsotrade.com"
    # smtp_cc = "luis.30200228@uru.edu"  # Correo en copia
    smtp_tls = os.getenv("SMTP_TLS", "true").lower() == "true"

    # Validar que las variables SMTP no sean None
    if not all([smtp_host, smtp_user, smtp_password, smtp_sender, smtp_to]):
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
    msg["To"] = str(smtp_to)
    # msg["Cc"] = str(smtp_cc)
    msg["Subject"] = subject
    msg.attach(MIMEText(body, "plain"))

    try:
        server = smtplib.SMTP(str(smtp_host), smtp_port)
        if smtp_tls:
            server.starttls()
        server.login(str(smtp_user), str(smtp_password))
        # Enviar a destinatario(s)
        to_addrs = [x.strip() for x in str(smtp_to).split(",") if x.strip()]
        server.sendmail(str(smtp_sender), to_addrs, msg.as_string())
        server.quit()
        return {"detail": "Mensaje enviado correctamente", "to": to_addrs}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error al enviar el correo: {str(e)}")
