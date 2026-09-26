import json

from fastapi import Depends, Header, HTTPException, status
from sqlalchemy.orm import Session

from app.core.security import decode_access_token, decode_access_token_with_grace
from app.db.session import get_db
from app.models import Admin, Customer

# 后台全部权限点，与前端 ADMIN_NAV 的 key 一一对应
ALL_PERMISSIONS = ['orders', 'verifications', 'fruits', 'stats', 'coupons', 'users', 'settings']

# 角色的默认权限集：账号未显式勾选权限（admins.permissions 为空）时按此回落
ROLE_PRESETS = {
    'super_admin': ALL_PERMISSIONS,
    'order_admin': ['orders'],
}


def admin_permissions(admin: Admin) -> list[str]:
    """账号实际权限点：显式勾选的 permissions 优先，为空则回落到角色预设。"""
    if admin.permissions:
        try:
            granted = json.loads(admin.permissions)
        except json.JSONDecodeError:
            granted = []
        allowed = [item for item in ALL_PERMISSIONS if item in granted]
        if allowed:
            return allowed
    return list(ROLE_PRESETS.get(admin.role or 'order_admin', ['orders']))


def get_current_admin(authorization: str | None = Header(default=None), db: Session = Depends(get_db)) -> Admin:
    if not authorization or not authorization.lower().startswith('bearer '):
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail='Missing admin token')

    token = authorization.split(' ', 1)[1]
    subject = decode_access_token(token)
    if not subject:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail='Invalid admin token')

    admin = db.query(Admin).filter(Admin.username == subject, Admin.is_active.is_(True)).first()
    if not admin:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail='Admin not found')
    return admin


def require_admin_permission(permission: str):
    def dependency(admin: Admin = Depends(get_current_admin)) -> Admin:
        if permission not in admin_permissions(admin):
            raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail='No permission')
        return admin
    return dependency


def get_optional_customer(
    x_customer_phone: str | None = Header(default=None),
    db: Session = Depends(get_db),
) -> Customer | None:
    if not x_customer_phone:
        return None
    return db.query(Customer).filter(Customer.phone == x_customer_phone).first()


def get_optional_auth_customer(authorization: str | None = Header(default=None), db: Session = Depends(get_db)) -> Customer | None:
    if not authorization or not authorization.lower().startswith('bearer '):
        return None
    token = authorization.split(' ', 1)[1]
    # Try strict decode first, then grace-period decode for recently expired tokens
    subject = decode_access_token(token) or decode_access_token_with_grace(token)
    if not subject or not subject.startswith('customer:'):
        return None
    try:
        customer_id = int(subject.split(':', 1)[1])
    except ValueError:
        return None
    return db.query(Customer).filter(Customer.id == customer_id).first()


def get_current_customer(
    customer: Customer | None = Depends(get_optional_auth_customer),
) -> Customer:
    if not customer:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail='Missing customer token')
    return customer
