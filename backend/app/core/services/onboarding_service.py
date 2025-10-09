from sqlalchemy.orm import Session
from app.db import models as m
from app.auth.security_passwords import hash_password
from app.db.queries.user_queries import get_user_by_email


class UserOnboardingService:
    @staticmethod
    def create_user_with_started_plan(db: Session, email: str, password: str) -> m.User:
        email = email.lower()
        if get_user_by_email(db, email):
            raise ValueError("Email ya registrado")
        user = m.User(email=email, password_hash=hash_password(password))
        db.add(user)
        db.commit()
        db.refresh(user)

        # Asegurar plan started
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
        db.add(m.Subscription(user_id=user.id, plan_id=plan.id, status="active"))
        db.commit()
        return user
