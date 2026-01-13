from fastapi import APIRouter, HTTPException, Depends
from pydantic import BaseModel, EmailStr, Field
from typing import List
from sqlalchemy.orm import Session
from app.db.database import get_db
from app.utils.adapters.email_adapter import async_send_email, EmailConfigError


router = APIRouter(prefix="/contact", tags=["contact"])


class SimpleContactForm(BaseModel):
    """Simplified contact form matching frontend fields."""
    name: str = Field(..., min_length=2, max_length=200)
    email: EmailStr
    phone: str | None = Field(None, max_length=30)
    company: str | None = Field(None, max_length=200)
    subject: str = Field(..., min_length=5, max_length=200)
    message: str = Field(..., min_length=10, max_length=2000)


def _compose_simple_body(data: SimpleContactForm) -> str:
    """Compose plain text email body."""
    lines = [
        "New contact form submission:",
        "",
        f"Name: {data.name}",
        f"Email: {data.email}",
        f"Phone: {data.phone or '-'}",
        f"Company: {data.company or '-'}",
        f"Subject: {data.subject}",
        "",
        "Message:",
        data.message,
    ]
    return "\n".join(lines)


def _compose_simple_html(data: SimpleContactForm) -> str:
    """Compose HTML email body."""
    return f"""
    <html>
    <body style='font-family: Arial, sans-serif; background: #f9f9f9; padding: 24px;'>
        <div style='max-width: 600px; margin: auto; background: #fff; border-radius: 8px; box-shadow: 0 2px 8px rgba(0,0,0,0.1); padding: 32px;'>
            <h2 style='color: #1a2233; margin-top: 0; border-bottom: 2px solid #e74c3c; padding-bottom: 12px;'>New Contact Form Submission</h2>
            
            <table style='width: 100%; border-collapse: collapse; font-size: 15px; margin-top: 20px;'>
                <tr>
                    <td style='font-weight: bold; padding: 8px 0; width: 120px; color: #555;'>Name:</td>
                    <td style='padding: 8px 0;'>{data.name}</td>
                </tr>
                <tr>
                    <td style='font-weight: bold; padding: 8px 0; color: #555;'>Email:</td>
                    <td style='padding: 8px 0;'><a href='mailto:{data.email}' style='color: #e74c3c;'>{data.email}</a></td>
                </tr>
                <tr>
                    <td style='font-weight: bold; padding: 8px 0; color: #555;'>Phone:</td>
                    <td style='padding: 8px 0;'>{data.phone or '-'}</td>
                </tr>
                <tr>
                    <td style='font-weight: bold; padding: 8px 0; color: #555;'>Company:</td>
                    <td style='padding: 8px 0;'>{data.company or '-'}</td>
                </tr>
                <tr>
                    <td style='font-weight: bold; padding: 8px 0; color: #555;'>Subject:</td>
                    <td style='padding: 8px 0;'><strong>{data.subject}</strong></td>
                </tr>
            </table>
            
            <div style='margin-top: 24px; padding: 16px; background: #f8f9fa; border-left: 4px solid #e74c3c; border-radius: 4px;'>
                <p style='margin: 0 0 8px 0; font-weight: bold; color: #555;'>Message:</p>
                <p style='margin: 0; white-space: pre-wrap; line-height: 1.6;'>{data.message}</p>
            </div>
            
            <div style='margin-top: 32px; padding-top: 16px; border-top: 1px solid #e0e0e0; color: #888; font-size: 13px; text-align: center;'>
                <em>Sent from HSO Marine contact form</em>
            </div>
        </div>
    </body>
    </html>
    """


@router.post("/simple-submit")
async def submit_simple_contact(form: SimpleContactForm, db: Session = Depends(get_db)):
    """
    Simplified contact form endpoint matching current frontend fields.
    Sends email to configured recipients and confirmation to user.
    """
    try:
        from app.config import settings as cfg
        
        # Check if contact forms are enabled
        if not cfg.ENABLE_CONTACT_FORMS:
            raise HTTPException(status_code=503, detail="Contact form is currently disabled")
        
        # Prepare email content
        subject = f"HSO Marine Contact: {form.subject}"
        body_text = _compose_simple_body(form)
        body_html = _compose_simple_html(form)
        
        # Get recipients from config
        recipients = cfg.EMAIL_TO
        if not recipients:
            raise HTTPException(status_code=500, detail="Email recipients not configured")
        
        # Get CC list if configured
        cc_list = []
        if hasattr(cfg, "SMTP_CC") and cfg.SMTP_CC:
            if isinstance(cfg.SMTP_CC, (list, tuple)):
                cc_list = list(cfg.SMTP_CC)
            else:
                cc_list = [email.strip() for email in str(cfg.SMTP_CC).split(",") if email.strip()]
        
        # Send email to recipients
        result = await async_send_email(
            subject,
            {"text": body_text, "html": body_html},
            to=recipients,
            cc=cc_list if cc_list else None,
            reply_to=form.email,
            from_email=cfg.SMTP_USER
        )
        
        # Send confirmation email to user
        user_mail = {"to": str(form.email), "sent": False, "error": None}
        try:
            user_subject = "HSO Marine — Thanks for contacting us"
            user_body_text = (
                f"Hi {form.name},\n\n"
                "Thank you for reaching out to HSO Marine. We have received your message and will get back to you shortly.\n\n"
                f"Your message:\n{form.message}\n\n"
                "Best regards,\n"
                "HSO Marine Team"
            )
            user_body_html = f"""
            <html>
            <body style='font-family: Arial, sans-serif; background: #f9f9f9; padding: 24px;'>
                <div style='max-width: 600px; margin: auto; background: #fff; border-radius: 8px; padding: 32px;'>
                    <h2 style='color: #1a2233; margin-top: 0;'>Thank You for Contacting HSO Marine</h2>
                    <p>Hi {form.name},</p>
                    <p>Thank you for reaching out to us. We have received your message and will get back to you shortly.</p>
                    <div style='margin: 20px 0; padding: 16px; background: #f8f9fa; border-radius: 4px;'>
                        <p style='margin: 0 0 8px 0; font-weight: bold;'>Your message:</p>
                        <p style='margin: 0; white-space: pre-wrap;'>{form.message}</p>
                    </div>
                    <p>Best regards,<br><strong>HSO Marine Team</strong></p>
                </div>
            </body>
            </html>
            """
            await async_send_email(
                user_subject,
                {"text": user_body_text, "html": user_body_html},
                to=[str(form.email)]
            )
            user_mail["sent"] = True
        except Exception as ue:
            user_mail["error"] = str(ue)
        
        return {
            "ok": True,
            "message": "Your message has been sent successfully",
            "recipients": recipients,
            "smtp_result": result,
            "userEmail": user_mail
        }
        
    except EmailConfigError as e:
        raise HTTPException(status_code=500, detail=f"Email configuration error: {e}")
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to send email: {e}")
