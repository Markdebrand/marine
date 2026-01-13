from fastapi import APIRouter, HTTPException, Depends
from pydantic import BaseModel, EmailStr, Field
from sqlalchemy.orm import Session
from app.db.database import get_db
from app.utils.adapters.email_adapter import async_send_email, EmailConfigError


router = APIRouter(prefix="/contact", tags=["support"])


class SupportForm(BaseModel):
    """Support form matching contact form fields."""
    name: str = Field(..., min_length=2, max_length=200)
    email: EmailStr
    phone: str | None = Field(None, max_length=30)
    company: str | None = Field(None, max_length=200)
    subject: str = Field(..., min_length=5, max_length=200)
    message: str = Field(..., min_length=10, max_length=2000)


def _compose_support_body(data: SupportForm) -> str:
    """Compose plain text email body for support."""
    lines = [
        "New support request:",
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


def _compose_support_html(data: SupportForm) -> str:
    """Compose HTML email body for support."""
    return f"""
    <html>
    <body style='font-family: Arial, sans-serif; background: #f9f9f9; padding: 24px;'>
        <div style='max-width: 600px; margin: auto; background: #fff; border-radius: 8px; box-shadow: 0 2px 8px rgba(0,0,0,0.1); padding: 32px;'>
            <h2 style='color: #1a2233; margin-top: 0; border-bottom: 2px solid #e74c3c; padding-bottom: 12px;'>New Support Request</h2>
            
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
            
            <div style='margin-top: 24px; padding: 16px; background: #fff3cd; border-left: 4px solid #ffc107; border-radius: 4px;'>
                <p style='margin: 0 0 8px 0; font-weight: bold; color: #856404;'>Support Request:</p>
                <p style='margin: 0; white-space: pre-wrap; line-height: 1.6; color: #333;'>{data.message}</p>
            </div>
            
            <div style='margin-top: 32px; padding-top: 16px; border-top: 1px solid #e0e0e0; color: #888; font-size: 13px; text-align: center;'>
                <em>Sent from HSO Marine support form</em>
            </div>
        </div>
    </body>
    </html>
    """


@router.post("/support-submit")
async def submit_support(form: SupportForm, db: Session = Depends(get_db)):
    """
    Support form endpoint - sends to support@hsomarine.com
    """
    try:
        from app.config import settings as cfg
        
        # Check if support forms are enabled
        if not cfg.ENABLE_SUPPORT_FORM:
            raise HTTPException(status_code=503, detail="Support form is currently disabled")
        
        # Prepare email content
        subject = f"HSO Marine Support: {form.subject}"
        body_text = _compose_support_body(form)
        body_html = _compose_support_html(form)
        
        # Get support recipients (defaults to support@hsomarine.com)
        import os
        support_email = os.getenv("SUPPORT_EMAIL_TO", "support@hsomarine.com")
        recipients = [support_email] if isinstance(support_email, str) else support_email
        
        # Send email to support team
        result = await async_send_email(
            subject,
            {"text": body_text, "html": body_html},
            to=recipients,
            reply_to=form.email,
            from_email=cfg.SMTP_USER
        )
        
        # Send confirmation email to user
        user_mail = {"to": str(form.email), "sent": False, "error": None}
        try:
            user_subject = "HSO Marine — Support Request Received"
            user_body_text = (
                f"Hi {form.name},\n\n"
                "Thank you for contacting HSO Marine Support. We have received your request and will respond as soon as possible.\n\n"
                f"Your request:\n{form.message}\n\n"
                "Best regards,\n"
                "HSO Marine Support Team"
            )
            user_body_html = f"""
            <html>
            <body style='font-family: Arial, sans-serif; background: #f9f9f9; padding: 24px;'>
                <div style='max-width: 600px; margin: auto; background: #fff; border-radius: 8px; padding: 32px;'>
                    <h2 style='color: #1a2233; margin-top: 0;'>Support Request Received</h2>
                    <p>Hi {form.name},</p>
                    <p>Thank you for contacting HSO Marine Support. We have received your request and will respond as soon as possible.</p>
                    <div style='margin: 20px 0; padding: 16px; background: #f8f9fa; border-radius: 4px;'>
                        <p style='margin: 0 0 8px 0; font-weight: bold;'>Your request:</p>
                        <p style='margin: 0; white-space: pre-wrap;'>{form.message}</p>
                    </div>
                    <p>Best regards,<br><strong>HSO Marine Support Team</strong></p>
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
            "message": "Your support request has been sent successfully",
            "recipients": recipients,
            "smtp_result": result,
            "userEmail": user_mail
        }
        
    except EmailConfigError as e:
        raise HTTPException(status_code=500, detail=f"Email configuration error: {e}")
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to send email: {e}")
