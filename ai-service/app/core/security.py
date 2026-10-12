import secrets
from fastapi import Header, HTTPException
from app.core.config import settings


def verify_key(x_internal_key: str = Header(default="")) -> None:
    """AI Service chỉ cho Spring Boot gọi: so khớp header X-Internal-Key."""
    if not secrets.compare_digest(x_internal_key, settings.internal_api_key):
        raise HTTPException(status_code=401, detail="Sai hoặc thiếu X-Internal-Key")
