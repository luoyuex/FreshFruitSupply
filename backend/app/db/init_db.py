from sqlalchemy.orm import Session

from app.core.security import hash_password
from app.db.session import Base, SessionLocal, engine
from app.models import Admin, Announcement, CouponTemplate, SystemSetting


def seed(db: Session) -> None:
    if not db.query(Admin).filter(Admin.username == 'admin').first():
        db.add(Admin(username='admin', password_hash=hash_password('admin123456'), role='super_admin'))

    settings = {
        'supplier_phone': '13800000000',
        'supplier_wechat': 'fruit-supplier',
        'notice': '价格随行情波动，提交预订后以电话确认为准。',
        # 配送费规则：商品原价合计低于 120 元收取 10 元配送费，可在后台修改
        'delivery_free_threshold': '120',
        'delivery_fee': '10',
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

    # 默认补送券示例：无金额/门槛，只手动发放，配货据券名/说明补配对应商品
    if not db.query(CouponTemplate).filter(CouponTemplate.kind == 'reissue').first():
        db.add(CouponTemplate(
            name='补送-坏果补配',
            description='坏果补配，随单免费补送对应商品',
            kind='reissue',
            discount_type='amount',
            amount=0,
            min_spend=0,
            valid_days=90,
            grant_on_verified=False,
            per_customer_limit=1,
            is_active=True,
        ))

    # 首次运行放一条欢迎公告，便于验证公告弹窗/历史/红点效果
    if not db.query(Announcement).first():
        db.add(Announcement(
            title='欢迎使用珍果链',
            content='价格随行情波动，提交预订后以电话确认为准。祝您采购顺利！',
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
