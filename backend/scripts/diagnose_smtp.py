import sys
import os
from pathlib import Path

# Add backend root to path to import app.config
current_dir = Path(__file__).resolve().parent
backend_root = current_dir.parent
sys.path.append(str(backend_root))

from app.config import settings as cfg
import smtplib
from email.message import EmailMessage

import time

def test_host(host, port, user, password):
    print(f"\nTesting Host: {host}:{port}")
    try:
        import socket
        resolved_ip = host
        try:
            addr_info = socket.getaddrinfo(host, port, socket.AF_INET)
            resolved_ip = addr_info[0][4][0]
            print(f"  [DNS] Resolved to IPv4: {resolved_ip}")
        except Exception as e:
            print(f"  [DNS] Resolution failed: {e}")
            return

        start = time.time()
        print(f"  [CONN] Connecting to {resolved_ip}...")
        server = smtplib.SMTP(resolved_ip, port, timeout=60)
        print(f"  [CONN] Connected in {time.time() - start:.2f}s")
        
        server.set_debuglevel(0) # Reduce noise
        
        start = time.time()
        server.ehlo()
        print(f"  [EHLO] OK in {time.time() - start:.2f}s")
        
        if cfg.SMTP_TLS:
            start = time.time()
            server.starttls()
            print(f"  [TLS] Started in {time.time() - start:.2f}s")
            server.ehlo()
        
        if user and password:
            start = time.time()
            print(f"  [AUTH] Authenticating as {user}...")
            server.login(user, password)
            print(f"  [AUTH] OK in {time.time() - start:.2f}s")
        
        server.quit()
        print(f"  [SUCCESS] Full handshake passed.")
        
    except Exception as e:
        print(f"  [FAIL] Error: {e}")

def diagnose():
    print("--- SMTP Connectivity Benchmark ---")
    hosts = [cfg.SMTP_HOST, "smtp.office365.com"]
    # unique hosts only
    hosts = list(dict.fromkeys(hosts))
    
    for h in hosts:
        test_host(h, cfg.SMTP_PORT, cfg.SMTP_USER, cfg.SMTP_PASSWORD)

if __name__ == "__main__":
    diagnose()
