"""
Script para crear usuarios de prueba y asignarles el rol 'user'.
Puedes ejecutarlo con:
    python -m app.scripts.create_test_users
"""
from app.db.database import SessionLocal
from app.db import models as m
from app.auth.security_passwords import hash_password

def main():
    db = SessionLocal()
    emails = [
        "user1@acme.com",
        "user2@acme.com",
        "user3@acme.com",
        "user4@acme.com"
    ]
    password = "Test1234!"  # Puedes cambiarlo
    hashed = hash_password(password)
    # Obtener role_id para 'user'
    role = db.query(m.Role).filter(m.Role.slug == "user").first()
    if not role:
        print("No existe el rol 'user'. Ejecuta el seeding primero.")
        return
    for email in emails:
        persona = m.User(email=email, password_hash=hashed, role="user", is_superadmin=False)
        db.add(persona)
        db.commit()
        db.refresh(persona)
        db.add(m.UserRole(user_id=persona.id, role_id=role.id))
        db.commit()
        print(f"Usuario creado: {email} (id={persona.id})")
    db.close()

if __name__ == "__main__":
    main()
