"""Email helpers for sharing invitations lifecycle.

Best-effort fire-and-forget helpers. They rely on existing async_send_email utility.
If email sending fails, we swallow exceptions (caller logs debug) to avoid
blocking core business flow.
"""
from __future__ import annotations

from typing import Dict, Any
from urllib.parse import urlencode

from app.utils.adapters.email_adapter import async_send_email
from app.config import settings as cfg

# Paths could be adjusted if frontend expects different route
_INVITE_FRONTEND_PATH = "/dashboard/verification"


def _build_invitation_link(token: str) -> str:
    base = cfg.FRONTEND_URL.rstrip("/")
    qp = urlencode({"token": token})
    return f"{base}{_INVITE_FRONTEND_PATH}?{qp}"


def _wrap_html(title: str, body: str, disclaimer: str) -> str:
    """Red themed wrapper (white body + red header)."""
    return f"""
    <meta http-equiv='Content-Type' content='text/html; charset=UTF-8' />
    <table width='100%' cellpadding='0' cellspacing='0' style='background:#ffffff;padding:32px;font-family:Arial,Helvetica,sans-serif;'>
        <tr>
            <td align='center'>
                <table width='100%' cellpadding='0' cellspacing='0' style='max-width:620px;background:#ffffff;border-radius:14px;overflow:hidden;box-shadow:0 6px 22px -4px rgba(0,0,0,0.25);border:1px solid #f1f5f9;'>
                    <tr>
                        <td style='background:linear-gradient(135deg,#dc2626,#b91c1c);padding:26px 30px;color:#fff;font-size:21px;font-weight:600;letter-spacing:.5px;'>
                            {title}
                        </td>
                    </tr>
                    <tr>
                        <td style='padding:30px 36px;color:#374151;font-size:15px;line-height:1.6;'>
                            {body}
                            <div style='margin-top:34px;font-size:12px;color:#6b7280;border-top:1px solid #e5e7eb;padding-top:18px;'>
                                {disclaimer}
                            </div>
                        </td>
                    </tr>
                </table>
            </td>
        </tr>
    </table>
    """.strip()


async def send_invitation_email(inviter_email: str, invitee_email: str, token: str, scopes: Dict[str, Any], lang: str | None = None):
    """Send invitation email (basic i18n via lang code)."""
    link = _build_invitation_link(token)
    l = (lang or "en").lower()
    if l.startswith("es"):
        subj = "Invitación segura para verificar y compartir datos financieros limitados"
        heading = "Invitación a HSOTrade"
        intro = ("El usuario <strong style='color:#b91c1c'>" + inviter_email + "</strong> te ha solicitado verificar tu identidad. "
                 "Al completar este proceso, podrás compartir de forma segura ciertos datos financieros de solo lectura con quien te envió esta invitación, exclusivamente para fines de verificación y revisión.")
        action_hint = "Pulsa el botón para iniciar la verificación y revisar los detalles de la solicitud. Podrás aceptar o rechazar el acceso en cualquier momento."
        button = "Iniciar verificación"
        alt = "Si el botón no funciona, utiliza este enlace directo seguro:"  # matches es translation key
        disclaimer1 = "Si no reconoces esta solicitud ignora este correo."
        disclaimer2 = "Este mensaje es confidencial y generado automáticamente. Si no lo solicitaste ignóralo."
    else:
        subj = "Secure invitation to verify and share limited financial data"
        heading = "HSOTrade Secure Invitation"
        intro = ("User <strong style='color:#b91c1c'>" + inviter_email + "</strong> has requested that you verify your identity. "
                 "After completing this process you can securely share limited read‑only financial data with the requester strictly for verification and review purposes.")
        action_hint = "Click the button to start the verification and review the request details. You can accept or decline at any time."
        button = "Start verification"
        alt = "If the button doesn’t work, use this secure direct link:"  # matches en translation key
        disclaimer1 = "If you do not recognize this request, ignore this email."
        disclaimer2 = "This message is confidential and automatically generated. If you did not request this, please disregard it."

    body = f"""
        <p style='margin:0 0 16px'>{intro}</p>
        <p style='margin:0 0 18px'>{action_hint}</p>
        <div style='text-align:center;margin:30px 0;'>
            <a href='{link}' style='display:inline-block;background:#dc2626;color:#fff;text-decoration:none;padding:15px 28px;border-radius:10px;font-weight:600;font-size:15px;font-family:Arial,Helvetica,sans-serif;box-shadow:0 3px 10px rgba(220,38,38,0.35)'>{button}</a>
        </div>
        <div style='margin:18px 0 0 0;font-size:13px;color:#374151;'>
            {alt}<br />
            <span style='display:inline-block;margin-top:7px;padding:8px 12px;background:#fef2f2;border:1px solid #fecaca;border-radius:6px;word-break:break-all;font-size:12px;color:#b91c1c'>{link}</span>
        </div>
        <p style='margin:24px 0 0;font-size:13px;color:#6b7280'>{disclaimer1}</p>
    """.strip()
    html = _wrap_html(heading, body, f"{disclaimer2}")
    await async_send_email(subj, {"text": html, "html": html}, to=[invitee_email])  # type: ignore[arg-type]


async def send_consent_granted_email(inviter_email: str, invitee_email: str, lang: str | None = None):
    l = (lang or "en").lower()
    if l.startswith("es"):
        subj = "Consentimiento otorgado"
        heading = subj
        body = f"""
            <p style='margin:0 0 16px'><strong>{invitee_email}</strong> ha aceptado la invitación y se registraron las capturas iniciales (snapshots) de los datos autorizados.</p>
            <p style='margin:0 0 16px'>Ahora puedes visualizar y realizar refresh periódico desde tu panel.</p>
        """.strip()
        disclaimer = "Mensaje generado automáticamente."
    else:
        subj = "Consent granted"
        heading = subj
        body = f"""
            <p style='margin:0 0 16px'><strong>{invitee_email}</strong> accepted the invitation and initial authorized data snapshots were captured.</p>
            <p style='margin:0 0 16px'>You can now view and refresh data periodically from your dashboard.</p>
        """.strip()
        disclaimer = "Automatically generated message."
    html = _wrap_html(heading, body, disclaimer)
    await async_send_email(subj, {"text": html, "html": html}, to=[inviter_email])  # type: ignore[arg-type]


async def send_revoked_email(invitee_email: str, inviter_email: str, lang: str | None = None):
    l = (lang or "en").lower()
    if l.startswith("es"):
        subj = "Acceso revocado"
        heading = subj
        body = f"""
            <p style='margin:0 0 16px'><strong>{inviter_email}</strong> ha revocado el acceso a sus datos compartidos.</p>
            <p style='margin:0 0 16px'>Las capturas históricas previas seguirán existiendo hasta limpieza programada, pero no habrá nuevas actualizaciones.</p>
        """.strip()
        disclaimer = "Mensaje generado automáticamente."
    else:
        subj = "Access revoked"
        heading = subj
        body = f"""
            <p style='margin:0 0 16px'><strong>{inviter_email}</strong> has revoked access to their shared data.</p>
            <p style='margin:0 0 16px'>Previous historical snapshots remain until scheduled cleanup, but no new updates will occur.</p>
        """.strip()
        disclaimer = "Automatically generated message."
    html = _wrap_html(heading, body, disclaimer)
    await async_send_email(subj, {"text": html, "html": html}, to=[invitee_email])  # type: ignore[arg-type]
