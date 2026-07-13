from fastapi import Depends, Header, HTTPException, status
from sqlalchemy.orm import Session

from app.core.security import decode_access_token
from app.db.session import get_db
from app.models import Admin, Customer

ADMIN_PERMISSIONS = {
    'super_admin': ['orders', 'verifications', 'fruits', 'stats', 'users', 'coupons', 'settings'],
    'order_admin': ['orders'],
}


def admin_permissions(admin: Admin) -> list[str]:
    return ADMIN_PERMISSIONS.get(admin.role or 'order_admin', ['orders'])


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
    subject = decode_access_token(token)
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
