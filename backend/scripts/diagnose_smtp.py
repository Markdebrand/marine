#!/usr/bin/env python3
"""
Diagnostic script to test SMTP connection with detailed error reporting.
Run this to see exactly where the SMTP connection is failing.
"""
import smtplib
import sys
from email.message import EmailMessage

# Load config from .env
import os
from pathlib import Path
from dotenv import load_dotenv

backend_root = Path(__file__).resolve().parents[1]
env_file = backend_root / ".env"
if env_file.exists():
    load_dotenv(dotenv_path=env_file)
    print(f"✓ Loaded config from {env_file}")
else:
    print(f"✗ No .env file found at {env_file}")
    sys.exit(1)

# Read SMTP config
smtp_host = os.getenv("SMTP_HOST")
smtp_port = int(os.getenv("SMTP_PORT", "587"))
smtp_user = os.getenv("SMTP_USER")
smtp_password = os.getenv("SMTP_PASSWORD")
smtp_tls = os.getenv("SMTP_TLS", "true").lower() in ("1", "true", "yes", "on")
smtp_ssl = os.getenv("SMTP_SSL", "false").lower() in ("1", "true", "yes", "on")
email_sender = os.getenv("EMAIL_SENDER")

print("\n" + "="*60)
print("SMTP Configuration Test")
print("="*60)
print(f"Host: {smtp_host}")
print(f"Port: {smtp_port}")
print(f"User: {smtp_user}")
print(f"Password: {'*' * len(smtp_password) if smtp_password else 'NOT SET'}")
print(f"TLS: {smtp_tls}")
print(f"SSL: {smtp_ssl}")
print(f"Sender: {email_sender}")
print("="*60 + "\n")

if not smtp_host:
    print("✗ ERROR: SMTP_HOST is not configured")
    sys.exit(1)

if not smtp_user or not smtp_password:
    print("✗ ERROR: SMTP_USER or SMTP_PASSWORD not configured")
    sys.exit(1)

try:
    print("Step 1: Connecting to SMTP server...")
    if smtp_ssl:
        print(f"  → Using SSL connection to {smtp_host}:{smtp_port}")
        server = smtplib.SMTP_SSL(smtp_host, smtp_port, timeout=15)
    else:
        print(f"  → Using plain connection to {smtp_host}:{smtp_port}")
        server = smtplib.SMTP(smtp_host, smtp_port, timeout=15)
        
    print("  ✓ Connected successfully\n")
    
    print("Step 2: EHLO handshake...")
    server.ehlo()
    print("  ✓ EHLO successful\n")
    
    if smtp_tls and not smtp_ssl:
        print("Step 3: Starting TLS encryption...")
        server.starttls()
        print("  ✓ TLS started successfully")
        server.ehlo()
        print("  ✓ EHLO after TLS successful\n")
    
    print("Step 4: Authenticating...")
    print(f"  → Logging in as {smtp_user}")
    server.login(smtp_user, smtp_password)
    print("  ✓ Authentication successful\n")
    
    print("Step 5: Sending test email...")
    msg = EmailMessage()
    msg["Subject"] = "Test Email from HSO Marine"
    msg["From"] = email_sender or smtp_user
    msg["To"] = smtp_user  # Send to yourself
    msg.set_content(f"""
This is a test email from the HSO Marine diagnostic script.
If you receive this, your SMTP configuration is working correctly!

Configuration used:
- Host: {smtp_host}
- Port: {smtp_port}
- User: {smtp_user}
- TLS: {smtp_tls}
""")
    
    result = server.send_message(msg)
    print(f"  ✓ Email sent successfully!")
    print(f"  → SMTP response: {result}")
    
    server.quit()
    print("\n" + "="*60)
    print("✓ ALL TESTS PASSED!")
    print("="*60)
    print(f"\nCheck your inbox at {smtp_user} for the test email.")
    
except smtplib.SMTPAuthenticationError as e:
    print(f"\n✗ AUTHENTICATION FAILED")
    print(f"  Error: {e}")
    print("\n" + "="*60)
    print("POSSIBLE SOLUTIONS:")
    print("="*60)
    print("1. If you have Multi-Factor Authentication (MFA) enabled:")
    print("   - You MUST use an App Password instead of your regular password")
    print("   - Generate one at: https://account.microsoft.com/security")
    print("   - Look for 'App passwords' or 'Contraseñas de aplicación'")
    print("")
    print("2. Enable SMTP AUTH for your mailbox:")
    print("   - Go to Microsoft 365 Admin Center")
    print("   - Users > Active users > Select your user")
    print("   - Mail tab > Manage email apps")
    print("   - Enable 'Authenticated SMTP'")
    print("")
    print("3. Check if your password is correct")
    print("   - Make sure there are no extra spaces")
    print("   - Passwords are case-sensitive")
    sys.exit(1)
    
except smtplib.SMTPConnectError as e:
    print(f"\n✗ CONNECTION FAILED")
    print(f"  Error: {e}")
    print("\n" + "="*60)
    print("POSSIBLE SOLUTIONS:")
    print("="*60)
    print("1. Check if port 587 is blocked by your firewall")
    print("2. Try using smtp-mail.outlook.com instead of smtp.office365.com")
    print("3. Verify your internet connection")
    sys.exit(1)
    
except smtplib.SMTPException as e:
    print(f"\n✗ SMTP ERROR")
    print(f"  Error: {e}")
    sys.exit(1)
    
except Exception as e:
    print(f"\n✗ UNEXPECTED ERROR")
    print(f"  Error type: {type(e).__name__}")
    print(f"  Error: {e}")
    import traceback
    print("\nFull traceback:")
    traceback.print_exc()
    sys.exit(1)
