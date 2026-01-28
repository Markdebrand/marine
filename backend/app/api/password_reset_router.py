from fastapi import APIRouter, HTTPException, Depends, Request
from pydantic import BaseModel, EmailStr, Field
from sqlalchemy.orm import Session
from app.db.database import get_db
from app.db.models.user import User
from app.core.services.password_reset_service import PasswordResetService
from app.utils.adapters.email_adapter import async_send_email, EmailConfigError
import os


router = APIRouter(prefix="/auth", tags=["authentication"])


class ForgotPasswordRequest(BaseModel):
    """Request model for forgot password endpoint."""
    email: EmailStr


class ResetPasswordRequest(BaseModel):
    """Request model for reset password endpoint."""
    token: str = Field(..., min_length=1)
    new_password: str = Field(..., min_length=8, max_length=100)


def _compose_password_reset_text(user_name: str, reset_link: str) -> str:
    """Compose plain text email body for password reset."""
    return f"""Hi {user_name},

You recently requested to reset your password for your HSO Marine account.

Click the link below to reset your password:
{reset_link}

This link will expire in 30 minutes.

If you did not request a password reset, please ignore this email or contact support if you have concerns.

Best regards,
HSO Marine Support Team
"""


def _compose_user_setup_text(user_name: str, setup_link: str) -> str:
    """Compose plain text email body for new user account setup."""
    return f"""Welcome to HSO Marine, {user_name}!

An administrator has created an account for you. To get started, you need to set up your password.

Click the link below to set your password and access your account:
{setup_link}

This setup link will expire in 7 days.

If you believe this email was sent in error, please disregard it.

Best regards,
HSO Marine Team
"""


def _compose_password_reset_html(user_name: str, reset_link: str) -> str:
    """Compose HTML email body for password reset."""
    return f"""
    <html>
    <body style='font-family: Arial, sans-serif; background: #f9f9f9; padding: 24px;'>
        <div style='max-width: 600px; margin: auto; background: #fff; border-radius: 8px; box-shadow: 0 2px 8px rgba(0,0,0,0.1); padding: 32px;'>
            <h2 style='color: #1a2233; margin-top: 0; border-bottom: 2px solid #e74c3c; padding-bottom: 12px;'>Password Reset Request</h2>
            
            <p>Hi {user_name},</p>
            
            <p>You recently requested to reset your password for your HSO Marine account.</p>
            
            <p>Click the button below to reset your password:</p>
            
            <div style='text-align: center; margin: 32px 0;'>
                <a href='{reset_link}' style='display: inline-block; background: #e74c3c; color: #fff; padding: 14px 32px; text-decoration: none; border-radius: 5px; font-weight: bold;'>Reset Password</a>
            </div>
            
            <p style='color: #666; font-size: 14px;'>Or copy and paste this link into your browser:</p>
            <p style='color: #e74c3c; word-break: break-all; font-size: 13px;'>{reset_link}</p>
            
            <div style='margin-top: 32px; padding: 16px; background: #fff3cd; border-left: 4px solid #ffc107; border-radius: 4px;'>
                <p style='margin: 0; font-size: 14px; color: #856404;'><strong>Important:</strong> This link will expire in 30 minutes.</p>
            </div>
            
            <p style='margin-top: 24px; color: #666; font-size: 13px;'>If you did not request a password reset, please ignore this email or contact support if you have concerns.</p>
            
            <div style='margin-top: 32px; padding-top: 16px; border-top: 1px solid #e0e0e0; color: #888; font-size: 13px; text-align: center;'>
                <em>Best regards,<br>HSO Marine Support Team</em>
            </div>
        </div>
    </body>
    </html>
    """


def _compose_user_setup_html(user_name: str, setup_link: str) -> str:
    """Compose HTML email body for new user account setup."""
    return f"""
    <html>
    <body style='font-family: Arial, sans-serif; background: #f4f7f9; padding: 24px;'>
        <div style='max-width: 600px; margin: auto; background: #fff; border-radius: 12px; box-shadow: 0 4px 20px rgba(0,0,0,0.08); padding: 40px; border: 1px solid #e1e8ed;'>
            <div style='text-align: center; margin-bottom: 32px;'>
                <h1 style='color: #1e293b; margin: 0; font-size: 24px; letter-spacing: -0.5px;'>Welcome to HSO Marine</h1>
            </div>
            
            <p style='color: #334155; font-size: 16px; line-height: 1.6;'>Hi {user_name},</p>
            
            <p style='color: #334155; font-size: 16px; line-height: 1.6;'>An administrator has created an account for you on the HSO Marine platform. To get started, you'll need to configure your password.</p>
            
            <div style='text-align: center; margin: 40px 0;'>
                <a href='{setup_link}' style='display: inline-block; background: #2563eb; color: #fff; padding: 16px 40px; text-decoration: none; border-radius: 8px; font-weight: 600; font-size: 16px; transition: background 0.2s;'>Set Up Password</a>
            </div>
            
            <p style='color: #64748b; font-size: 14px;'>Or copy and paste this link into your browser:</p>
            <p style='background: #f8fafc; padding: 12px; border-radius: 6px; border: 1px solid #f1f5f9; color: #2563eb; word-break: break-all; font-size: 13px; font-family: monospace;'>{setup_link}</p>
            
            <div style='margin-top: 32px; padding: 16px; background: #eff6ff; border-radius: 8px; border-left: 4px solid #3b82f6;'>
                <p style='margin: 0; font-size: 14px; color: #1e40af;'><strong>Tip:</strong> This setup link is valid for 7 days. After that, you'll need to use the "Forgot Password" feature to gain access.</p>
            </div>
            
            <div style='margin-top: 40px; padding-top: 24px; border-top: 1px solid #f1f5f9; color: #94a3b8; font-size: 13px; text-align: center;'>
                <p style='margin: 0;'>Thank you for joining us!<br><strong>The HSO Marine Team</strong></p>
            </div>
        </div>
    </body>
    </html>
    """


def _compose_password_changed_text(user_name: str) -> str:
    """Compose plain text email body for password change confirmation."""
    return f"""Hi {user_name},

Your password has been successfully changed.

If you did not make this change, please contact our support team immediately.

Best regards,
HSO Marine Support Team
"""


def _compose_password_changed_html(user_name: str) -> str:
    """Compose HTML email body for password change confirmation."""
    return f"""
    <html>
    <body style='font-family: Arial, sans-serif; background: #f9f9f9; padding: 24px;'>
        <div style='max-width: 600px; margin: auto; background: #fff; border-radius: 8px; box-shadow: 0 2px 8px rgba(0,0,0,0.1); padding: 32px;'>
            <h2 style='color: #1a2233; margin-top: 0; border-bottom: 2px solid #27ae60; padding-bottom: 12px;'>Password Changed Successfully</h2>
            
            <p>Hi {user_name},</p>
            
            <p>Your password has been successfully changed.</p>
            
            <div style='margin: 24px 0; padding: 16px; background: #d4edda; border-left: 4px solid #28a745; border-radius: 4px;'>
                <p style='margin: 0; color: #155724;'><strong>✓ Your account is now secured with your new password.</strong></p>
            </div>
            
            <div style='margin-top: 24px; padding: 16px; background: #fff3cd; border-left: 4px solid #ffc107; border-radius: 4px;'>
                <p style='margin: 0; font-size: 14px; color: #856404;'><strong>Didn't make this change?</strong> Please contact our support team immediately.</p>
            </div>
            
            <div style='margin-top: 32px; padding-top: 16px; border-top: 1px solid #e0e0e0; color: #888; font-size: 13px; text-align: center;'>
                <em>Best regards,<br>HSO Marine Support Team</em>
            </div>
        </div>
    </body>
    </html>
    """


@router.post("/forgot-password")
async def forgot_password(
    request_body: ForgotPasswordRequest,
    request: Request,
    db: Session = Depends(get_db)
):
    """
    Request a password reset. Sends an email with a reset link.
    Always returns success for security (doesn't reveal if email exists).
    """
    email_clean = request_body.email.strip().lower()
    try:
        from app.config import settings as cfg
        
        # Find user by email (case-insensitive)
        user = db.query(User).filter(User.email == email_clean).first()
        
        # Always return success, even if user doesn't exist (security best practice)
        if not user:
            print(f"[PASSWORD_RESET] User not found for email: {email_clean}")
            return {
                "ok": True,
                "message": "If that email exists in our system, we've sent a password reset link."
            }
        
        # Get client IP for audit trail
        client_ip = request.client.host if request.client else None
        
        # Generate reset token
        expiry_minutes = getattr(cfg, 'PASSWORD_RESET_TOKEN_EXPIRY_MINUTES', 30)
        token = PasswordResetService.generate_reset_token(
            user.id,
            db,
            expiry_minutes=expiry_minutes,
            ip_address=client_ip
        )
        
        # Generate reset link
        reset_url_template = getattr(
            cfg, 
            'PASSWORD_RESET_FRONTEND_URL',
            f"{cfg.FRONTEND_URL}/reset-password?token={{token}}"
        )
        reset_link = reset_url_template.format(token=token)
        
        # Prepare email content
        user_name = user.first_name or user.email.split('@')[0]
        subject = "HSO Marine — Password Reset Request"
        body_text = _compose_password_reset_text(user_name, reset_link)
        body_html = _compose_password_reset_html(user_name, reset_link)
        
        # Send email
        print(f"[PASSWORD_RESET] Sending recovery email to: {user.email}")
        await async_send_email(
            subject,
            {"text": body_text, "html": body_html},
            to=[user.email],
            from_email=cfg.SMTP_USER
        )
        
        return {
            "ok": True,
            "message": "If that email exists in our system, we've sent a password reset link."
        }
        
    except EmailConfigError as e:
        print(f"[PASSWORD_RESET][ERROR] SMTP Configuration error: {e}")
        raise HTTPException(status_code=500, detail=f"Email configuration error: {e}")
    except Exception as e:
        # Log the error but don't expose details to user
        import traceback
        print(f"[PASSWORD_RESET][ERROR] Failed to process forgot password request for {email_clean}: {e}")
        print(traceback.format_exc())
        return {
            "ok": True,
            "message": "If that email exists in our system, we've sent a password reset link."
        }


@router.post("/reset-password")
async def reset_password(
    request_body: ResetPasswordRequest,
    db: Session = Depends(get_db)
):
    """
    Reset password using a valid token.
    """
    try:
        from app.config import settings as cfg
        
        # Validate token
        user = PasswordResetService.validate_reset_token(request_body.token, db)
        
        if not user:
            raise HTTPException(
                status_code=400,
                detail="Invalid or expired reset token"
            )
        
        # Reset password
        PasswordResetService.reset_user_password(user.id, request_body.new_password, db)
        
        # Mark token as used
        PasswordResetService.mark_token_as_used(request_body.token, db)
        
        # Send confirmation email
        user_name = user.first_name or user.email.split('@')[0]
        subject = "HSO Marine — Password Changed Successfully"
        body_text = _compose_password_changed_text(user_name)
        body_html = _compose_password_changed_html(user_name)
        
        try:
            await async_send_email(
                subject,
                {"text": body_text, "html": body_html},
                to=[user.email],
                from_email=cfg.SMTP_USER
            )
        except Exception as e:
            # Log but don't fail the request if confirmation email fails
            print(f"[PASSWORD_RESET][WARNING] Failed to send confirmation email: {e}")
        
        return {
            "ok": True,
            "message": "Password has been reset successfully. You can now log in with your new password."
        }
        
    except HTTPException:
        raise
    except Exception as e:
        print(f"[PASSWORD_RESET][ERROR] Failed to reset password: {e}")
        raise HTTPException(status_code=500, detail="Failed to reset password. Please try again.")


@router.get("/verify-reset-token/{token}")
async def verify_reset_token(
    token: str,
    db: Session = Depends(get_db)
):
    """
    Verify if a reset token is valid (without using it).
    Useful for frontend to check token before showing reset form.
    """
    user = PasswordResetService.validate_reset_token(token, db)
    
    if not user:
        raise HTTPException(
            status_code=400,
            detail="Invalid or expired reset token"
        )
    
    return {
        "ok": True,
        "valid": True,
        "message": "Token is valid"
    }
