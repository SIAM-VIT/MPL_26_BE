from typing import Optional
from fastapi import HTTPException, Header

from app.core.config import settings


def verify_admin(
    admin_passcode: Optional[str] = Header(None, alias="admin-passcode"),
    x_admin_passcode: Optional[str] = Header(None, alias="x-admin-passcode"),
    authorization: Optional[str] = Header(None, alias="Authorization"),
):
    passcode = admin_passcode or x_admin_passcode
    if not passcode and authorization:
        if authorization.startswith("Bearer "):
            passcode = authorization[7:].strip()
        else:
            passcode = authorization.strip()

    if not passcode or passcode != settings.ADMIN_PASSCODE:
        raise HTTPException(status_code=401, detail="Unauthorized: Invalid admin passcode")
