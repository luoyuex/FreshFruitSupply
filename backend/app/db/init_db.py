from sqlalchemy.orm import Session

from app.core.security import hash_password
from app.db.session import Base, SessionLocal, engine
from app.models import Admin, CouponTemplate, SystemSetting


def seed(db: Session) -> None:
    if not db.query(Admin).filter(Admin.username == 'admin').first():
        db.add(Admin(username='admin', password_hash=hash_password('admin123456'), role='super_admin'))

    settings = {
        'supplier_phone': '13800000000',
        'supplier_wechat': 'fruit-supplier',
        'notice': '价格随行情波动，提交预订后以电话确认为准。',
    }
    for key, value in settings.items():
        if not db.query(SystemSetting).filter(SystemSetting.key == key).first():
            db.add(SystemSetting(key=key, value=value))

    # 默认「认证送券」模板：认证通过自动发放满100减10、有效期30天，后台可再改/停用
    if not db.query(CouponTemplate).filter(CouponTemplate.grant_on_verified.is_(True)).first():
        db.add(CouponTemplate(
            name='认证专享券',
            description='完成商家认证后自动发放',
            discount_type='amount',
            amount=10,
            min_spend=100,
            valid_days=30,
            grant_on_verified=True,
            per_customer_limit=1,
            is_active=True,
        ))

    db.commit()


def main() -> None:
    Base.metadata.create_all(bind=engine)
    db = SessionLocal()
    try:
        seed(db)
    finally:
        db.close()


if __name__ == '__main__':
    main()
