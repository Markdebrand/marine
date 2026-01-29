from fastapi import APIRouter, HTTPException, Depends
from pydantic import BaseModel, EmailStr, Field
from sqlalchemy.orm import Session
from app.db.database import get_db
from app.utils.adapters.email_adapter import async_send_email, EmailConfigError
from app.db import models


router = APIRouter(prefix="/registration", tags=["registration"])


class StartMarineRegistration(BaseModel):
    """Start Marine registration form."""
    first_name: str = Field(..., min_length=2, max_length=100)
    last_name: str = Field(..., min_length=2, max_length=100)
    email: EmailStr
    phone: str = Field(..., min_length=7, max_length=30)
    company: str | None = Field(None, max_length=200)
    plan_id: int
    billing_period: str


def _compose_registration_body(data: StartMarineRegistration, plan_name: str) -> str:
    """Compose plain text email body for registration."""
    lines = [
        "New Start Marine Registration:",
        "",
        f"Name: {data.first_name} {data.last_name}",
        f"Email: {data.email}",
        f"Phone: {data.phone}",
        f"Company: {data.company or '-'}",
        f"Plan: {plan_name}",
        f"Billing Period: {data.billing_period}",
        "",
        "Please follow up with this lead as soon as possible.",
    ]
    return "\n".join(lines)


def _compose_registration_html(data: StartMarineRegistration, plan_name: str) -> str:
    """Compose HTML email body for registration."""
    return f"""
    <html>
    <body style='font-family: Arial, sans-serif; background: #f9f9f9; padding: 24px;'>
        <div style='max-width: 600px; margin: auto; background: #fff; border-radius: 8px; box-shadow: 0 2px 8px rgba(0,0,0,0.1); padding: 32px;'>
            <h2 style='color: #1a2233; margin-top: 0; border-bottom: 2px solid #e74c3c; padding-bottom: 12px;'>New Start Marine Registration</h2>
            
            <table style='width: 100%; border-collapse: collapse; font-size: 15px; margin-top: 20px;'>
                <tr>
                    <td style='font-weight: bold; padding: 8px 0; width: 120px; color: #555;'>Name:</td>
                    <td style='padding: 8px 0;'>{data.first_name} {data.last_name}</td>
                </tr>
                <tr>
                    <td style='font-weight: bold; padding: 8px 0; color: #555;'>Email:</td>
                    <td style='padding: 8px 0;'><a href='mailto:{data.email}' style='color: #e74c3c;'>{data.email}</a></td>
                </tr>
                <tr>
                    <td style='font-weight: bold; padding: 8px 0; color: #555;'>Phone:</td>
                    <td style='padding: 8px 0;'><a href='tel:{data.phone}' style='color: #e74c3c;'>{data.phone}</a></td>
                </tr>
                <tr>
                    <td style='font-weight: bold; padding: 8px 0; color: #555;'>Company:</td>
                    <td style='padding: 8px 0;'>{data.company or '-'}</td>
                </tr>
                <tr>
                    <td style='font-weight: bold; padding: 8px 0; color: #555;'>Plan:</td>
                    <td style='padding: 8px 0;'>{plan_name}</td>
                </tr>
                <tr>
                    <td style='font-weight: bold; padding: 8px 0; color: #555;'>Billing Period:</td>
                    <td style='padding: 8px 0;'>{data.billing_period}</td>
                </tr>
            </table>
            
            <div style='margin-top: 24px; padding: 16px; background: #fff3cd; border-left: 4px solid #ffc107; border-radius: 4px;'>
                <p style='margin: 0; font-weight: bold; color: #856404;'>⚡ Action Required: Please follow up with this lead as soon as possible.</p>
            </div>
            
            <div style='margin-top: 32px; padding-top: 16px; border-top: 1px solid #e0e0e0; color: #888; font-size: 13px; text-align: center;'>
                <em>Sent from HSO Marine registration form</em>
            </div>
        </div>
    </body>
    </html>
    """


@router.get("/plans")
def get_plans(db: Session = Depends(get_db)):
    """
    Get all available plans.
    """
    plans = db.query(models.Plan).all()
    return [{"id": p.id, "name": p.name} for p in plans]


@router.post("/start-marine")
async def register_start_marine(form: StartMarineRegistration, db: Session = Depends(get_db)):
    """
    Start Marine registration endpoint - sends to info@hsomarine.com
    """
    try:
        from app.config import settings as cfg
        
        # Get plan name from DB
        plan = db.query(models.Plan).filter(models.Plan.id == form.plan_id).first()
        plan_name = plan.name if plan else f"Unknown (ID: {form.plan_id})"
        
        # Prepare email content for sales team
        subject = f"New Start Marine Registration: {form.first_name} {form.last_name}"
        body_text = _compose_registration_body(form, plan_name)
        body_html = _compose_registration_html(form, plan_name)
        
        # Get recipients (defaults to info@hsomarine.com)
        import os
        registration_email = os.getenv("REGISTRATION_EMAIL_TO", "info@hsomarine.com")
        recipients = [registration_email] if isinstance(registration_email, str) else registration_email
        
        # Send email to sales team
        result = await async_send_email(
            subject,
            {"text": body_text, "html": body_html},
            to=recipients,
            reply_to=form.email,
            from_email=cfg.SMTP_USER
        )
        
        # Send welcome email to user
        user_mail = {"to": str(form.email), "sent": False, "error": None}
        try:
            user_subject = "Welcome to HSO Marine!"
            user_body_text = (
                f"Hi {form.first_name},\n\n"
                "Thank you for your interest in HSO Marine! We're excited to help you unlock your full trading potential.\n\n"
                "Our team will be in touch with you shortly to get you started.\n\n"
                "In the meantime, if you have any questions, feel free to reach out to us.\n\n"
                "Best regards,\n"
                "The HSO Marine Team"
            )
            user_body_html = f"""
            <html>
            <body style='font-family: Arial, sans-serif; background: #f9f9f9; padding: 24px;'>
                <div style='max-width: 600px; margin: auto; background: #fff; border-radius: 8px; padding: 32px;'>
                    <h2 style='color: #1a2233; margin-top: 0;'>Welcome to HSO Marine!</h2>
                    <p>Hi {form.first_name},</p>
                    <p>Thank you for your interest in HSO Marine! We're excited to help you unlock your full trading potential.</p>
                    <p>Our team will be in touch with you shortly to get you started.</p>
                    <p>In the meantime, if you have any questions, feel free to reach out to us.</p>
                    <p>Best regards,<br><strong>The HSO Marine Team</strong></p>
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
            "message": "Registration successful! Our team will contact you shortly.",
            "recipients": recipients,
            "smtp_result": result,
            "userEmail": user_mail
        }
        
    except EmailConfigError as e:
        raise HTTPException(status_code=500, detail=f"Email configuration error: {e}")
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to process registration: {e}")
