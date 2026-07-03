from sqlalchemy.orm import Session

from app.core.security import hash_password
from app.db.session import Base, SessionLocal, engine
from app.models import Admin, SystemSetting


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
