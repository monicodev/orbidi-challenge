from datetime import datetime, timedelta, timezone
from typing import Annotated, Optional
from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPBearer
from jose import JWTError, jwt
from app.core.config import settings

security_scheme = HTTPBearer()

def create_access_token(data: dict, expires_delta: Optional[timedelta] = None):
    """Generates a JWT token."""
    to_encode = data.copy()
    if expires_delta:
        expire = datetime.now(timezone.utc) + expires_delta
    else:
        expire = datetime.now(timezone.utc) + timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)
    
    to_encode.update({"exp": expire})
    encoded_jwt = jwt.encode(to_encode, settings.SECRET_KEY, algorithm=settings.ALGORITHM)
    return encoded_jwt

async def get_current_user(token: Annotated[str, Depends(security_scheme)]):
    """
    Validates the token.
    """
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )
    try:
        token_str = token.credentials 
        payload = jwt.decode(token_str, settings.SECRET_KEY, algorithms=[settings.ALGORITHM])
        
        username: str = payload.get("sub")
        if username is None:
            raise credentials_exception
            
        return username
    except (JWTError, AttributeError):
        raise credentials_exception
    