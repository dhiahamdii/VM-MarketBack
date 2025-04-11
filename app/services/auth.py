from datetime import datetime, timedelta
from typing import Optional
from jose import JWTError, jwt
from passlib.context import CryptContext
from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from sqlalchemy.orm import Session
import logging
import os
from ..models.user import User
from ..database import get_db

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Security configurations
SECRET_KEY = "7739234248a1ae37e22c6b4b3e2ce77d8e196629d0cb32be4f65006376c2a064ca4839de3242780dc7ac82eb41ab83f21234cde65e39c3c26f7dc4b57cee619302569a821f1a77c7daa4d275a830076db1bbbce07754fe22f62ea885927bae54dc57e5ef483d68e666e7a5ae46bd72a34c4b9b3de8c50113bbcba5980aceb3807ce0585467e9357fde44568f580471fc1cf6ea8d8bb1b4ef68687eea886d63ad4853df527c78f67baee3a95b4f91c4e7adc8e6f30e684fd0d3b3ba7680e54baa1b2337435bb3a814cc6cb75f682ccd6ded579d15257894efeb41cf84333613ff4c4733c5dcb4a632b82e439d638ca4f0874e1827a2e697d9b88787b30cbc0cba"
REFRESH_SECRET_KEY = "35d70d2dd59a6c823e2a9a0b147d9ab56c2a3df4f38015448294eaad103472ff506ed0d34dbed84de981ad950693fe83444125a31fb4eac77e991719eab5e225de80c1045957582122f865c0a09f2f442407e407653208d2370e57b2b28a7b3ec7bec87fbb28109594042178ce644ff605a00c07d4968417642b5a4d51ac744dcfd9d54fbb3fd152c8cd8ff40cb1c597bfacf1ac04d5cf1e73f2eb8cf7de1c52524de1eeec95dde02a6134df68e0a2f73446a04bd7f51b16ee45eb0c0f420e1f948befc724898fdec0b514ecf8dc8134935c13f51dbfd2dcac26ecae7db1345a5baffc2900e447d37d327964feab4fa7a80d46653a45436975f8a627c5edbc28"
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 30
REFRESH_TOKEN_EXPIRE_DAYS = 7

# Configure password hashing
pwd_context = CryptContext(
    schemes=["bcrypt"],
    deprecated="auto",
    bcrypt__rounds=12
)

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="auth/login")

def verify_password(plain_password: str, hashed_password: str) -> bool:
    try:
        logger.info("Verifying password")
        result = pwd_context.verify(plain_password, hashed_password)
        logger.info(f"Password verification result: {result}")
        return result
    except Exception as e:
        logger.error(f"Password verification error: {str(e)}")
        return False

def get_password_hash(password: str) -> str:
    try:
        logger.info("Hashing password")
        return pwd_context.hash(password)
    except Exception as e:
        logger.error(f"Password hashing error: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Password hashing failed"
        )

def create_access_token(data: dict, expires_delta: Optional[timedelta] = None) -> str:
    try:
        to_encode = data.copy()
        if expires_delta:
            expire = datetime.utcnow() + expires_delta
        else:
            expire = datetime.utcnow() + timedelta(minutes=15)
        to_encode.update({"exp": expire})
        encoded_jwt = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
        return encoded_jwt
    except Exception as e:
        logger.error(f"Access token creation error: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Token creation failed"
        )

def create_refresh_token(data: dict, expires_delta: Optional[timedelta] = None) -> str:
    try:
        to_encode = data.copy()
        if expires_delta:
            expire = datetime.utcnow() + expires_delta
        else:
            expire = datetime.utcnow() + timedelta(days=7)
        to_encode.update({"exp": expire})
        encoded_jwt = jwt.encode(to_encode, REFRESH_SECRET_KEY, algorithm=ALGORITHM)
        return encoded_jwt
    except Exception as e:
        logger.error(f"Refresh token creation error: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Refresh token creation failed"
        )

def verify_refresh_token(token: str) -> Optional[str]:
    try:
        payload = jwt.decode(token, REFRESH_SECRET_KEY, algorithms=[ALGORITHM])
        email: str = payload.get("sub")
        if email is None:
            return None
        return email
    except JWTError:
        return None

async def get_current_user(
    token: str = Depends(oauth2_scheme),
    db: Session = Depends(get_db)
) -> User:
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        email: str = payload.get("sub")
        if email is None:
            raise credentials_exception
    except JWTError:
        raise credentials_exception
    user = db.query(User).filter(User.email == email).first()
    if user is None:
        raise credentials_exception
    return user

def authenticate_user(email: str, password: str, db: Session) -> Optional[User]:
    user = db.query(User).filter(User.email == email).first()
    if not user:
        return None
    if not verify_password(password, user.hashed_password):
        return None
    return user 