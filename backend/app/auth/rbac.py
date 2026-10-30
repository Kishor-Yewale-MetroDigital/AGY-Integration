from enum import StrEnum

from fastapi import Depends, Header, HTTPException, status
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.database import get_db
from app.models.entities import ApprovalDelegation, HiringRequest, User


class Role(StrEnum):
    REQUEST_CREATOR = "REQUEST_CREATOR"
    HIRING_MANAGER = "HIRING_MANAGER"
    HRBP = "HRBP"
    FINANCE_REVIEWER = "FINANCE_REVIEWER"
    COMMITTEE_MEMBER = "COMMITTEE_MEMBER"
    ADMIN = "ADMIN"
    EXEC_READONLY = "EXEC_READONLY"


STAGE_ALLOWED_ROLES: dict[str, set[str]] = {
    "MANAGER_REVIEW": {Role.HIRING_MANAGER, Role.HRBP},
    "FINANCE_REVIEW": {Role.FINANCE_REVIEWER},
    "COMMITTEE_PENDING": {Role.COMMITTEE_MEMBER},
}


def get_current_user(
    x_user_id: str | None = Header(default=None, alias="X-User-Id"),
    x_user_email: str | None = Header(default=None, alias="X-User-Email"),
    db: Session = Depends(get_db),
) -> User:
    user: User | None = None
    if x_user_id:
        user = db.get(User, x_user_id)
    elif x_user_email:
        user = db.scalar(select(User).where(User.email == x_user_email))
    else:
        # Default to initial Hiring Manager in dev/demo if header omitted
        user = db.scalar(select(User).where(User.role == Role.HIRING_MANAGER))

    if not user or not user.is_active:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Authenticated active user required via X-User-Id or X-User-Email header.",
        )
    return user


def require_roles(*allowed_roles: Role):
    allowed = {str(r) for r in allowed_roles}

    def dependency(current_user: User = Depends(get_current_user)) -> User:
        if current_user.role == Role.EXEC_READONLY and Role.EXEC_READONLY not in allowed:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Executive Read-Only role is prohibited from performing write or workflow operations.",
            )
        if current_user.role not in allowed and current_user.role != Role.ADMIN:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"Role '{current_user.role}' is not authorized. Allowed roles: {sorted(allowed)}",
            )
        return current_user

    return dependency


def verify_stage_permission(
    db: Session,
    user: User,
    hiring_request: HiringRequest,
    stage_name: str,
) -> str | None:
    """
    Enforces RBAC and Segregation of Duties (SoD) for workflow stage approvals.
    Returns `delegated_from_id` if acting under an active delegation, or None if direct.
    """
    if user.role == Role.EXEC_READONLY:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Executive Read-Only users cannot approve, reject, or modify workflow stages.",
        )

    # Segregation of Duties: Request owner cannot approve their own request
    if hiring_request.request_owner_id == user.id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Segregation of Duties violation: Request creators cannot approve their own hiring requests.",
        )

    allowed_roles = STAGE_ALLOWED_ROLES.get(stage_name, set())
    if user.role in allowed_roles or user.role == Role.ADMIN:
        return None

    # Check if an authorized user for this stage has delegated authority to `user`
    delegation = db.scalar(
        select(ApprovalDelegation).where(
            ApprovalDelegation.to_user_id == user.id,
            ApprovalDelegation.stage_name == stage_name,
            ApprovalDelegation.is_active.is_(True),
        )
    )
    if delegation:
        if delegation.from_user_id == hiring_request.request_owner_id:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Segregation of Duties violation: Cannot exercise delegated authority from the request creator.",
            )
        return delegation.from_user_id

    raise HTTPException(
        status_code=status.HTTP_403_FORBIDDEN,
        detail=(
            f"User '{user.email}' with role '{user.role}' is not authorized to act on stage '{stage_name}'. "
            f"Required roles: {sorted(allowed_roles)}"
        ),
    )
