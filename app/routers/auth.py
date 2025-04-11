from fastapi import APIRouter, Depends, HTTPException, status, Response
from fastapi.security import OAuth2PasswordBearer, OAuth2PasswordRequestForm
from sqlalchemy.orm import Session
from datetime import timedelta
import logging
from ..models.user import User as UserModel, UserRole
from ..database import get_db
from ..services.auth import (
    verify_password,
    get_password_hash,
    create_access_token,
    ACCESS_TOKEN_EXPIRE_MINUTES,
    create_refresh_token,
    verify_refresh_token,
    get_current_user,
    authenticate_user,
    REFRESH_TOKEN_EXPIRE_DAYS
)
from ..schemas.auth import Token, TokenData, UserCreate, User as UserSchema
from typing import Any

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

router = APIRouter()

# Security configurations
SECRET_KEY = "7739234248a1ae37e22c6b4b3e2ce77d8e196629d0cb32be4f65006376c2a064ca4839de3242780dc7ac82eb41ab83f21234cde65e39c3c26f7dc4b57cee619302569a821f1a77c7daa4d275a830076db1bbbce07754fe22f62ea885927bae54dc57e5ef483d68e666e7a5ae46bd72a34c4b9b3de8c50113bbcba5980aceb3807ce0585467e9357fde44568f580471fc1cf6ea8d8bb1b4ef68687eea886d63ad4853df527c78f67baee3a95b4f91c4e7adc8e6f30e684fd0d3b3ba7680e54baa1b2337435bb3a814cc6cb75f682ccd6ded579d15257894efeb41cf84333613ff4c4733c5dcb4a632b82e439d638ca4f0874e1827a2e697d9b88787b30cbc0cba"  # Change this to a secure secret key
REFRESH_SECRET_KEY = "35d70d2dd59a6c823e2a9a0b147d9ab56c2a3df4f38015448294eaad103472ff506ed0d34dbed84de981ad950693fe83444125a31fb4eac77e991719eab5e225de80c1045957582122f865c0a09f2f442407e407653208d2370e57b2b28a7b3ec7bec87fbb28109594042178ce644ff605a00c07d4968417642b5a4d51ac744dcfd9d54fbb3fd152c8cd8ff40cb1c597bfacf1ac04d5cf1e73f2eb8cf7de1c52524de1eeec95dde02a6134df68e0a2f73446a04bd7f51b16ee45eb0c0f420e1f948befc724898fdec0b514ecf8dc8134935c13f51dbfd2dcac26ecae7db1345a5baffc2900e447d37d327964feab4fa7a80d46653a45436975f8a627c5edbc28"  # Change this to a secure secret key
ALGORITHM = "HS256"

@router.post("/register", response_model=UserSchema)
def register(user: UserCreate, db: Session = Depends(get_db)) -> Any:
    try:
        # Check if user already exists
        db_user = db.query(UserModel).filter(UserModel.email == user.email).first()
        if db_user:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Email already registered"
            )
        
        # Create new user
        hashed_password = get_password_hash(user.password)
        db_user = UserModel(
            email=user.email,
            name=user.name,
            hashed_password=hashed_password,
            role=UserRole.USER,
            is_active=True
        )
        db.add(db_user)
        db.commit()
        db.refresh(db_user)
        return db_user
    except Exception as e:
        logger.error(f"Registration error: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Registration failed"
        )

@router.post("/login", response_model=Token)
def login(
    form_data: OAuth2PasswordRequestForm = Depends(),
    db: Session = Depends(get_db)
) -> Any:
    try:
        # Use the username field as email since OAuth2PasswordRequestForm uses username
        user = authenticate_user(form_data.username, form_data.password, db)
        if not user:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Incorrect email or password",
                headers={"WWW-Authenticate": "Bearer"},
            )
        if not user.is_active:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Inactive user"
            )
        
        access_token_expires = timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
        refresh_token_expires = timedelta(days=REFRESH_TOKEN_EXPIRE_DAYS)
        
        access_token = create_access_token(
            data={"sub": user.email},
            expires_delta=access_token_expires
        )
        refresh_token = create_refresh_token(
            data={"sub": user.email},
            expires_delta=refresh_token_expires
        )
        
        return {
            "access_token": access_token,
            "refresh_token": refresh_token,
            "token_type": "bearer"
        }
    except Exception as e:
        logger.error(f"Login error: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Login failed"
        )

@router.get("/me", response_model=UserSchema)
def read_users_me(current_user: UserModel = Depends(get_current_user)) -> Any:
    return current_user

@router.post("/refresh", response_model=Token)
async def refresh_access_token(
    response: Response,
    current_user: UserModel = Depends(get_current_user)
):
    try:
        new_access_token = create_access_token(
            data={"sub": current_user.email},
            expires_delta=timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
        )
        
        response.set_cookie(
            key="auth_token",
            value=new_access_token,
            httponly=True,
            secure=True,
            samesite="strict",
            max_age=ACCESS_TOKEN_EXPIRE_MINUTES * 60
        )
        
        return {"access_token": new_access_token, "token_type": "bearer"}
    except Exception as e:
        logger.error(f"Token refresh failed: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Could not refresh token",
        )

@router.post("/logout")
async def logout(response: Response):
    response.delete_cookie("auth_token")
    response.delete_cookie("refresh_token")
    return {"message": "Successfully logged out"} 