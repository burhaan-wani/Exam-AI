import logging
from datetime import datetime, timedelta, timezone
from fastapi import APIRouter, HTTPException
from passlib.context import CryptContext
from jose import jwt

from app.config import get_settings
from app.database import users_collection
from app.models.schemas import UserCreate, UserLogin, TokenResponse, UserOut

logger = logging.getLogger(__name__)
router = APIRouter()
settings = get_settings()
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")


def _create_token(data: dict) -> str:
    to_encode = data.copy()
    expire = datetime.now(timezone.utc) + timedelta(minutes=settings.access_token_expire_minutes)
    to_encode.update({"exp": expire})
    return jwt.encode(to_encode, settings.secret_key, algorithm="HS256")


@router.post("/register", response_model=TokenResponse)
async def register(body: UserCreate):
    existing = await users_collection.find_one({"email": body.email})
    if existing:
        raise HTTPException(400, "Email already registered")

    hashed = pwd_context.hash(body.password)
    doc = {
        "name": body.name,
        "email": body.email,
        "password_hash": hashed,
        "role": body.role.value,
        "created_at": datetime.now(timezone.utc).isoformat(),
    }
    result = await users_collection.insert_one(doc)
    user_id = str(result.inserted_id)

    token = _create_token({"sub": user_id, "role": body.role.value})
    logger.info(f"User registered: {body.email}")
    return TokenResponse(
        access_token=token,
        user=UserOut(id=user_id, name=body.name, email=body.email, role=body.role),
    )


@router.post("/login", response_model=TokenResponse)
async def login(body: UserLogin):
    user = await users_collection.find_one({"email": body.email})
    if not user or not pwd_context.verify(body.password, user.get("password_hash", "")):
        raise HTTPException(401, "Invalid email or password")

    user_id = str(user["_id"])
    role = user.get("role", "teacher")
    token = _create_token({"sub": user_id, "role": role})
    logger.info(f"User logged in: {body.email}")
    return TokenResponse(
        access_token=token,
        user=UserOut(id=user_id, name=user["name"], email=user["email"], role=role),
    )
