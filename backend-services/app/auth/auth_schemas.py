from pydantic import BaseModel, EmailStr, Field, model_validator

class RegisterRequest(BaseModel):
    email: EmailStr
    password: str = Field(min_length=6)
    password_confirmation: str = Field(min_length=6)

    @model_validator(mode="after")
    def passwords_match(self):  # type: ignore
        if self.password != self.password_confirmation:
            raise ValueError("passwords do not match")
        return self

class LoginRequest(BaseModel):
    email: EmailStr
    password: str

class TokenResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"
    refresh_token: str | None = None

class UserInfo(BaseModel):
    id: int
    email: EmailStr
    is_superadmin: bool | None = None

class RegisterResponse(UserInfo):
    pass


class RefreshRequest(BaseModel):
    refresh_token: str


# Perfil extendido con plan/rol para el frontend
class ProfileResponse(BaseModel):
    id: int
    email: EmailStr | None = None
    role: str  # 'admin' | 'user'
    is_superadmin: bool | None = None
    first_name: str | None = None
    last_name: str | None = None
    phone: str | None = None
    company: str | None = None
    website: str | None = None
    bio: str | None = None
    plan_code: str | None = None
    plan_name: str | None = None
    subscription_id: int | None = None
    subscription_status: str | None = None


class ProfileUpdate(BaseModel):
    first_name: str | None = None
    last_name: str | None = None
    phone: str | None = None
    company: str | None = None
    website: str | None = None
    bio: str | None = None


class SessionEntry(BaseModel):
    id: int | None = None
    created_at: str
    last_seen_at: str | None = None
    revoked_at: str | None = None
    active_seconds: int | None = None
    ip: str | None = None
    user_agent: str | None = None
