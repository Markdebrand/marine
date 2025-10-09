from fastapi import APIRouter, HTTPException, status, Request
from pydantic import BaseModel, EmailStr
from app.utils.adapters.email_adapter import async_send_email, EmailConfigError

router = APIRouter()

class SupportForm(BaseModel):
    name: str
    email: EmailStr
    subject: str
    message: str

@router.post("/support", status_code=status.HTTP_200_OK)
async def support(form: SupportForm, request: Request):
    subject = f"[Support] {form.subject}"
    # Plain text fallback
    body_text = (
        f"Name: {form.name}\n"
        f"Email: {form.email}\n"
        f"Subject: {form.subject}\n"
        f"Message: {form.message}"
    )

    # HTML formatted email
    body_html = f"""
    <html>
    <body style='font-family: Arial, sans-serif; background: #f9f9f9; padding: 24px;'>
        <div style='max-width: 520px; margin: auto; background: #fff; border-radius: 8px; box-shadow: 0 2px 8px #0001; padding: 32px;'>
            <h2 style='color: #b91c1c; margin-top: 0;'>New Support Request</h2>
            <table style='width: 100%; border-collapse: collapse; font-size: 15px;'>
                <tr><td style='font-weight: bold; padding: 6px 0;'>Name:</td><td>{form.name}</td></tr>
                <tr><td style='font-weight: bold; padding: 6px 0;'>Email:</td><td>{form.email}</td></tr>
                <tr><td style='font-weight: bold; padding: 6px 0;'>Subject:</td><td>{form.subject}</td></tr>
                <tr><td style='font-weight: bold; padding: 6px 0; vertical-align: top;'>Message:</td><td style='white-space: pre-line;'>{form.message}</td></tr>
            </table>
        </div>
    </body>
    </html>
    """
    try:
        cc = ["luis.mariojarabavillalobos@gmail.com"]
        await async_send_email(subject, {"text": body_text, "html": body_html}, None, None, None, cc) # type: ignore
        return {"detail": "Support request sent successfully"}
    except EmailConfigError as e:
        raise HTTPException(status_code=500, detail=f"SMTP config error: {str(e)}")
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to send support email: {str(e)}")
