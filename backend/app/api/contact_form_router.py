from fastapi import APIRouter, HTTPException, status, Request
from pydantic import BaseModel, EmailStr
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
async def contact_us(form: ContactForm, request: Request):
    from app.utils.adapters.email_adapter import async_send_email

    subject = f"Nuevo mensaje de Contact Us: {form.subject}"
    body = (
        f"Nombre: {form.name}\n"
        f"Teléfono: {form.phone}\n"
        f"Email: {form.email}\n"
        f"Empresa: {form.company}\n"
        f"Asunto: {form.subject}\n"
        f"Pregunta: {form.question}"
    )

    try:
        # async_send_email handles recipients from config and uses central SMTP logic
        # We pass None for recipients to use default EMAIL_TO/CONTACT_FORM_TO
        await async_send_email(subject, body)
        return {"detail": "Mensaje enviado correctamente"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error al enviar el correo: {str(e)}")
