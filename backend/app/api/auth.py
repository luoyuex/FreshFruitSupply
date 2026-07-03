from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.core.security import create_access_token
from app.db.session import get_db
from app.models import Customer
from app.schemas import CustomerAuthOut, WechatLoginIn
from app.services.wechat import code_to_session

router = APIRouter(prefix='/auth')


def _placeholder_phone(openid: str) -> str:
    return f'wx:{openid}'[:32]


def _is_phone_bound(customer: Customer) -> bool:
    return bool(customer.phone and not customer.phone.startswith('wx:'))


@router.post('/wechat-login', response_model=CustomerAuthOut)
def wechat_login(payload: WechatLoginIn, db: Session = Depends(get_db)):
    session = code_to_session(payload.code)
    openid = session['openid']
    customer = db.query(Customer).filter(Customer.wechat_openid == openid).first()
    if not customer:
        customer = Customer(
            phone=_placeholder_phone(openid),
            wechat_openid=openid,
            verification_status='unverified',
        )
        db.add(customer)
        db.commit()
        db.refresh(customer)
    token = create_access_token(f'customer:{customer.id}')
    return CustomerAuthOut(access_token=token, customer=customer, is_phone_bound=_is_phone_bound(customer))
