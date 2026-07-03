from sqlalchemy.orm import Session

from app.models import Customer


def get_or_create_customer(db: Session, phone: str, wechat_openid: str | None = None) -> Customer:
    customer = db.query(Customer).filter(Customer.phone == phone).first()
    if customer:
        if wechat_openid and not customer.wechat_openid:
            customer.wechat_openid = wechat_openid
        return customer

    customer = Customer(phone=phone, wechat_openid=wechat_openid, verification_status='unverified')
    db.add(customer)
    db.flush()
    return customer
