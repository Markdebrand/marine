from sqlalchemy.orm import Session
from app.db import models as m
from app.auth.security_passwords import hash_password
from app.db.queries.user_queries import get_user_by_email
from datetime import datetime, timezone
import calendar


class UserOnboardingService:
    @staticmethod
    def create_user_with_started_plan(db: Session, email: str, password: str | None = None, **kwargs) -> m.User:
        email = email.lower()
        if get_user_by_email(db, email):
            raise ValueError("Email ya registrado")
        
        # Si no hay password, generamos uno aleatorio largo para seguridad base
        # El usuario lo cambiará mediante el setup token
        if not password:
            import secrets
            password = secrets.token_urlsafe(32)
        
        # Filtrar campos permitidos para el modelo User
        user_fields = {
            "email": email,
            "password_hash": hash_password(password),
            "role": kwargs.get("role"),
            "first_name": kwargs.get("first_name"),
            "last_name": kwargs.get("last_name"),
            "phone": kwargs.get("phone"),
            "company": kwargs.get("company"),
            "website": kwargs.get("website"),
            "bio": kwargs.get("bio"),
            "plan_id": kwargs.get("plan_id"),
            "billing_period": kwargs.get("billing_period"),
        }
        # Eliminar valores None para dejar que actúen los defaults del modelo
        user_fields = {k: v for k, v in user_fields.items() if v is not None}
        
        user = m.User(**user_fields)
        db.add(user)
        db.commit()
        db.refresh(user)

        # Manejo de suscripción
        plan_id = kwargs.get("plan_id")
        if not plan_id:
            # Asegurar plan started por defecto si no se especificó uno
            plan = db.query(m.Plan).filter(m.Plan.code == "started").first()
            if not plan:
                plan = m.Plan(
                    code="started",
                    name="Started",
                    support="BASIC",
                    features={"dashboards": {"max": 3}},
                )
                db.add(plan)
                db.commit()
                db.refresh(plan)
            plan_id = plan.id

        # Calcular cancel_at si hay billing_period
        cancel_at = None
        billing_period = kwargs.get("billing_period")
        if billing_period:
            months_map = {
                "Monthly": 1,
                "Quarterly": 3,
                "Semiannual": 6,
                "Annual": 12
            }
            months_to_add = months_map.get(billing_period)
            if months_to_add:
                now = datetime.now(timezone.utc)
                # Lógica para añadir meses calendario
                month = now.month - 1 + months_to_add
                year = now.year + month // 12
                month = month % 12 + 1
                day = min(now.day, calendar.monthrange(year, month)[1])
                cancel_at = now.replace(year=year, month=month, day=day)

        db.add(m.Subscription(
            user_id=user.id, 
            plan_id=plan_id, 
            status="active",
            cancel_at=cancel_at
        ))
        db.commit()
        return user
