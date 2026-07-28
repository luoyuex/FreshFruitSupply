from datetime import datetime, timedelta, timezone

from jose import JWTError, jwt
from passlib.context import CryptContext

from app.core.config import settings

pwd_context = CryptContext(schemes=['bcrypt'], deprecated='auto')


def hash_password(password: str) -> str:
    return pwd_context.hash(password)


def verify_password(password: str, password_hash: str) -> bool:
    return pwd_context.verify(password, password_hash)


def create_access_token(subject: str) -> str:
    expires = datetime.now(timezone.utc) + timedelta(minutes=settings.jwt_expire_minutes)
    payload = {'sub': subject, 'exp': expires}
    return jwt.encode(payload, settings.jwt_secret_key, algorithm=settings.jwt_algorithm)


def decode_access_token(token: str) -> str | None:
    """Decode access token with strict expiry check."""
    return _decode_token(token, allow_expired=False)


def decode_access_token_with_grace(token: str) -> str | None:
    """Decode access token allowing tokens expired within the grace period."""
    return _decode_token(token, allow_expired=True)


def _decode_token(token: str, allow_expired: bool = False) -> str | None:
    try:
        payload = jwt.decode(
            token,
            settings.jwt_secret_key,
            algorithms=[settings.jwt_algorithm],
            options={'verify_exp': not allow_expired},
        )
        subject = payload.get('sub')
        if not subject:
            return None
        # If we skipped expiry check, still verify it's within grace period
        if allow_expired:
            exp = payload.get('exp')
            if exp is not None:
                exp_time = datetime.fromtimestamp(exp, tz=timezone.utc)
                grace_deadline = exp_time + timedelta(minutes=settings.jwt_refresh_grace_minutes)
                if datetime.now(timezone.utc) > grace_deadline:
                    return None  # Outside grace period — truly expired
        return str(subject)
    except JWTError:
        return None
