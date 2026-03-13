from typing import Any

from bson import ObjectId
from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from jose import JWTError, jwt

from app.config import get_settings
from app.database import users_collection
from app.models.schemas import UserRole

settings = get_settings()
security = HTTPBearer(auto_error=False)


def _unauthorized(detail: str = "Authentication required") -> HTTPException:
    return HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail=detail,
        headers={"WWW-Authenticate": "Bearer"},
    )


async def get_current_user(
    credentials: HTTPAuthorizationCredentials = Depends(security),
) -> dict[str, Any]:
    if credentials is None or credentials.scheme.lower() != "bearer":
        raise _unauthorized()

    token = credentials.credentials
    try:
        payload = jwt.decode(token, settings.secret_key, algorithms=["HS256"])
        user_id = payload.get("sub")
        if not user_id:
            raise _unauthorized("Invalid token payload")
    except JWTError:
        raise _unauthorized("Invalid or expired token")

    try:
        oid = ObjectId(user_id)
    except Exception:
        raise _unauthorized("Invalid token subject")

    user = await users_collection.find_one({"_id": oid})
    if not user:
        raise _unauthorized("User not found")

    return {
        "id": str(user["_id"]),
        "name": user.get("name", ""),
        "email": user.get("email", ""),
        "role": user.get("role", UserRole.TEACHER.value),
    }


def require_role(required_role: UserRole):
    async def _role_dependency(current_user: dict[str, Any] = Depends(get_current_user)) -> dict[str, Any]:
        if current_user["role"] != required_role.value:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"{required_role.value.capitalize()} access required",
            )
        return current_user

    return _role_dependency


require_teacher = require_role(UserRole.TEACHER)
require_student = require_role(UserRole.STUDENT)
