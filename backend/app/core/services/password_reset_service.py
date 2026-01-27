from __future__ import annotations

import secrets
import hashlib
from datetime import datetime, timedelta, timezone
from sqlalchemy.orm import Session
from typing import Optional

from app.db.models.password_reset_token import PasswordResetToken
from app.db.models.user import User
from app.auth.security_passwords import hash_password


class PasswordResetService:
    """Service for managing password reset tokens and operations."""
    
    @staticmethod
    def _hash_token(token: str) -> str:
        """Hash a token using SHA-256 for secure storage."""
        return hashlib.sha256(token.encode()).hexdigest()
    
    @staticmethod
    def generate_reset_token(
        user_id: int, 
        db: Session,
        expiry_minutes: int = 30,
        ip_address: Optional[str] = None
    ) -> str:
        """
        Generate a new password reset token for a user.
        
        Args:
            user_id: ID of the user requesting password reset
            db: Database session
            expiry_minutes: Token expiration time in minutes (default: 30)
            ip_address: Optional IP address for audit trail
            
        Returns:
            The plain-text token (to be sent via email)
        """
        # Generate a secure random token (32 bytes = 256 bits)
        token = secrets.token_urlsafe(32)
        
        # Hash the token before storing
        token_hash = PasswordResetService._hash_token(token)
        
        # Create expiration timestamp
        expires_at = datetime.now(timezone.utc) + timedelta(minutes=expiry_minutes)
        
        # Invalidate any existing unused tokens for this user
        PasswordResetService.invalidate_user_tokens(user_id, db)
        
        # Create and store the token
        reset_token = PasswordResetToken(
            user_id=user_id,
            token_hash=token_hash,
            expires_at=expires_at,
            ip_address=ip_address
        )
        db.add(reset_token)
        db.commit()
        
        return token
    
    @staticmethod
    def validate_reset_token(token: str, db: Session) -> Optional[User]:
        """
        Validate a reset token and return the associated user if valid.
        
        Args:
            token: The plain-text token to validate
            db: Database session
            
        Returns:
            User object if token is valid, None otherwise
        """
        # Hash the provided token
        token_hash = PasswordResetService._hash_token(token)
        
        # Find the token in database
        reset_token = db.query(PasswordResetToken).filter(
            PasswordResetToken.token_hash == token_hash
        ).first()
        
        if not reset_token:
            return None
        
        # Check if token has been used
        if reset_token.used_at is not None:
            return None
        
        # Check if token has expired
        if reset_token.expires_at < datetime.now(timezone.utc):
            return None
        
        # Return the associated user
        return reset_token.user
    
    @staticmethod
    def mark_token_as_used(token: str, db: Session) -> None:
        """
        Mark a token as used.
        
        Args:
            token: The plain-text token to mark as used
            db: Database session
        """
        token_hash = PasswordResetService._hash_token(token)
        
        reset_token = db.query(PasswordResetToken).filter(
            PasswordResetToken.token_hash == token_hash
        ).first()
        
        if reset_token:
            reset_token.used_at = datetime.now(timezone.utc)
            db.commit()
    
    @staticmethod
    def invalidate_user_tokens(user_id: int, db: Session) -> None:
        """
        Invalidate all unused tokens for a user.
        
        Args:
            user_id: ID of the user
            db: Database session
        """
        # Mark all unused tokens as used
        db.query(PasswordResetToken).filter(
            PasswordResetToken.user_id == user_id,
            PasswordResetToken.used_at.is_(None)
        ).update({"used_at": datetime.now(timezone.utc)})
        db.commit()
    
    @staticmethod
    def reset_user_password(user_id: int, new_password: str, db: Session) -> None:
        """
        Reset a user's password.
        
        Args:
            user_id: ID of the user
            new_password: New password in plain text
            db: Database session
        """
        user = db.query(User).filter(User.id == user_id).first()
        if user:
            user.password_hash = hash_password(new_password)
            db.commit()
