#!/usr/bin/env python
"""Utility script to generate a bcrypt hash.

No depende de importar el paquete app para evitar errores ModuleNotFoundError.

Uso:
  python scripts/hash_password.py <password>
  python scripts/hash_password.py   (te pedirá la contraseña oculta)
"""
from getpass import getpass
import sys
from passlib.context import CryptContext
from passlib.exc import MissingBackendError

# Debe coincidir con app.auth.security
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

def hash_password(password: str) -> str:
    return pwd_context.hash(password)

def main():
    if len(sys.argv) >= 2:
        password = sys.argv[1]
    else:
        password = getpass("Password: ")
    try:
        hashed = hash_password(password)
    except MissingBackendError:
        print("ERROR: Falta backend bcrypt. Instala dependencias dentro del entorno Python:\n  pip install -r requirements.txt\n")
        return
    print(hashed)

if __name__ == "__main__":
    main()
