from fastapi import APIRouter, HTTPException, Depends
from pydantic import BaseModel, EmailStr, Field
from typing import List
from sqlalchemy.orm import Session
from app.db.database import get_db


from app.utils.adapters.email_adapter import async_send_email, EmailConfigError


router = APIRouter(prefix="/contact", tags=["contact"])


class ContactForm(BaseModel):
    first_name: str = Field(..., min_length=1)
    last_name: str = Field(..., min_length=1)
    phone: str | None = None
    email: EmailStr
    company: str = Field(..., min_length=1)
    country: str = Field(..., min_length=1)
    job_title: str = Field(..., min_length=1)
    employees: str = Field(..., min_length=1)
    industry: str = Field(..., min_length=1)
    subscription: List[str] = Field(default_factory=list)
    geographic: str = Field(..., min_length=1)


def _compose_body(data: ContactForm) -> str:
    lines = [
        "New contact form submission:",
        "",
        f"Name: {data.first_name} {data.last_name}",
        f"Email: {data.email}",
        f"Phone: {data.phone or '-'}",
        f"Company: {data.company}",
        f"Job Title: {data.job_title}",
        f"Employees: {data.employees}",
        f"Country: {data.country}",
        f"Industry: {data.industry}",
        f"Geographic coverage: {data.geographic}",
        f"Subscription interests: {', '.join(data.subscription) if data.subscription else '-'}",
    ]
    return "\n".join(lines)

def _compose_html(data: ContactForm) -> str:
        # Simple, clean HTML table layout
        return f"""
        <html>
        <body style='font-family: Arial, sans-serif; background: #f9f9f9; padding: 24px;'>
            <div style='max-width: 520px; margin: auto; background: #fff; border-radius: 8px; box-shadow: 0 2px 8px #0001; padding: 32px;'>
                <h2 style='color: #1a2233; margin-top: 0;'>New Contact Form Submission</h2>
                <table style='width: 100%; border-collapse: collapse; font-size: 15px;'>
                    <tr><td style='font-weight: bold; padding: 6px 0;'>Name:</td><td>{data.first_name} {data.last_name}</td></tr>
                    <tr><td style='font-weight: bold; padding: 6px 0;'>Email:</td><td>{data.email}</td></tr>
                    <tr><td style='font-weight: bold; padding: 6px 0;'>Phone:</td><td>{data.phone or '-'}</td></tr>
                    <tr><td style='font-weight: bold; padding: 6px 0;'>Company:</td><td>{data.company}</td></tr>
                    <tr><td style='font-weight: bold; padding: 6px 0;'>Job Title:</td><td>{data.job_title}</td></tr>
                    <tr><td style='font-weight: bold; padding: 6px 0;'>Employees:</td><td>{data.employees}</td></tr>
                    <tr><td style='font-weight: bold; padding: 6px 0;'>Country:</td><td>{data.country}</td></tr>
                    <tr><td style='font-weight: bold; padding: 6px 0;'>Industry:</td><td>{data.industry}</td></tr>
                    <tr><td style='font-weight: bold; padding: 6px 0;'>Geographic coverage:</td><td>{data.geographic}</td></tr>
                    <tr><td style='font-weight: bold; padding: 6px 0;'>Subscription interests:</td><td>{', '.join(data.subscription) if data.subscription else '-'}</td></tr>
                </table>
                <div style='margin-top: 32px; color: #888; font-size: 13px;'>
                    <em>Sent from the HSO Marine web contact form.</em>
                </div>
            </div>
        </body>
        </html>
        """


@router.post("/submit")
async def submit_contact(form: ContactForm, db: Session = Depends(get_db)):
    try:
        # No persistence in DB
        subject = "HSO Marine — Contact form"
        body_text = _compose_body(form)
        body_html = _compose_html(form)
        # Enviar a EMAIL_TO y CC si está definido
        from app.config import settings as cfg
        recipients = cfg.EMAIL_TO
        cc_list = []
        if hasattr(cfg, "SMTP_CC") and cfg.SMTP_CC:
            # Permitir múltiples correos separados por coma o lista
            if isinstance(cfg.SMTP_CC, (list, tuple)):
                cc_list = list(cfg.SMTP_CC)
            else:
                cc_list = [email.strip() for email in str(cfg.SMTP_CC).split(",") if email.strip()]
        # reply_to: correo del usuario
        # Usar el correo SMTP configurado como remitente (from_email)
        result = await async_send_email(
            subject,
            {"text": body_text, "html": body_html},  # type: ignore[arg-type]
            to=recipients,
            cc=cc_list if cc_list else None,
            reply_to=form.email,
            from_email=cfg.SMTP_USER  # Siempre el usuario SMTP configurado
        )

        # 3) Enviar también un correo de prueba al usuario que llenó el formulario (no bloquear en caso de error)
        user_mail = {"to": str(form.email), "sent": False, "error": None}
        try:
            user_subject = "HSO Marine — Thanks for contacting us (test)"
            user_body_text = (
                f"Hi {form.first_name},\n\n"
                "Thanks for reaching out to HSO Marine. This is a test confirmation email to let you know your request was received.\n\n"
                "We will get back to you shortly.\n\n"
                "— HSO Marine Team"
            )
            await async_send_email(user_subject, {"text": user_body_text}, to=[str(form.email)])  # type: ignore[arg-type]
            user_mail["sent"] = True
        except Exception as ue:
            user_mail["error"] = str(ue)

        return {"ok": True, "recipients": recipients, "smtp_result": result, "userEmail": user_mail}
    except EmailConfigError as e:
        raise HTTPException(status_code=500, detail=f"Email configuration error: {e}")
    except Exception as e:
        # Devuelve el error SMTP completo para depuración
        raise HTTPException(status_code=500, detail=f"Failed to send email: {e}")
