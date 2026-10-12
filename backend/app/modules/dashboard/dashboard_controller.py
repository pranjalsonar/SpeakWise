from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.constants.roles import RoleId
from app.db.session import get_db
from app.middleware.auth_middleware import require_roles
from app.middleware.jwt_handler import TokenPayload
from app.modules.dashboard import dashboard_service
from app.modules.dashboard.dashboard_schemas import AdminDashboardResponse

router = APIRouter(prefix="/admin/dashboard", tags=["Admin dashboard"])


@router.get("", response_model=AdminDashboardResponse)
def get_admin_dashboard(
    _admin: TokenPayload = Depends(require_roles(RoleId.ADMIN)),
    db: Session = Depends(get_db),
):
    """KPIs, weekly session counts, category split and recent sessions (admin only)."""
    return dashboard_service.get_admin_dashboard(db)
