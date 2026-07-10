import json
from datetime import datetime, time
from zoneinfo import ZoneInfo
from decimal import Decimal

from fastapi import APIRouter, Depends, File, Form, HTTPException, UploadFile, status
from sqlalchemy.orm import Session, joinedload

from app.api.deps import get_optional_auth_customer
from app.db.session import get_db
from app.models import Customer, CustomerAddress, CustomerVerification, Fruit, FruitCategory, Order, OrderItem
from app.schemas import CustomerAddressOut, CustomerAddressUpsert, CustomerOut, CustomerProfileUpdate, FruitCategoryOut, FruitOut, OrderCreate, OrderOut, VerificationOut
from app.services.customer import get_or_create_customer
from app.services.email import send_order_email
from app.services.upload import save_upload, to_public_urls

router = APIRouter()
ORDER_EDIT_CUTOFF = time(22, 30)
EDITABLE_ORDER_STATUSES = {'pending', 'confirmed'}


def _is_before_order_edit_cutoff() -> bool:
    return datetime.now(ZoneInfo('Asia/Shanghai')).time() < ORDER_EDIT_CUTOFF


def _assert_order_editable(order: Order) -> None:
    if order.status not in EDITABLE_ORDER_STATUSES:
        raise HTTPException(status_code=400, detail='Order cannot be edited in current status')
    if not _is_before_order_edit_cutoff():
        raise HTTPException(status_code=400, detail='Orders cannot be edited after 22:30')


def _apply_order_payload(order: Order, customer: Customer, payload: OrderCreate, db: Session) -> None:
    if not payload.items:
        raise HTTPException(status_code=400, detail='Order must contain at least one item')

    order.receiver_name = payload.receiver_name
    order.receiver_phone = payload.receiver_phone
    order.province = payload.province
    order.city = payload.city
    order.district = payload.district
    order.detail_address = payload.detail_address
    order.delivery_note = payload.delivery_note

    order.items.clear()
    estimated_total = Decimal('0')
    for line in payload.items:
        fruit = db.query(Fruit).options(joinedload(Fruit.quote), joinedload(Fruit.category_ref)).filter(Fruit.id == line.fruit_id).first()
        if not fruit or not fruit.quote:
            raise HTTPException(status_code=404, detail=f'Fruit {line.fruit_id} not found')
        if fruit.stock_status == 'out_of_stock':
            raise HTTPException(status_code=400, detail=f'{fruit.name} is out of stock')

        price = fruit.quote.verified_price if customer.verification_status == 'verified' else fruit.quote.normal_price
        subtotal = price * line.quantity
        estimated_total += subtotal
        order.items.append(OrderItem(
            fruit_id=fruit.id,
            fruit_name=fruit.name,
            spec=fruit.spec,
            unit=fruit.unit,
            price=price,
            quantity=line.quantity,
            subtotal=subtotal,
        ))
    order.estimated_total = estimated_total


def _order_no() -> str:
    return datetime.now().strftime('F%Y%m%d%H%M%S%f')[:-3]


def _verification_payload(verification: CustomerVerification) -> dict:
    return {
        'id': verification.id,
        'customer_id': verification.customer_id,
        'shop_name': verification.shop_name,
        'contact_name': verification.contact_name,
        'phone': verification.phone,
        'business_type': verification.business_type,
        'image_urls': to_public_urls(json.loads(verification.image_urls or '[]')),
        'status': verification.status,
        'review_note': verification.review_note,
        'created_at': verification.created_at,
    }


def _current_customer_or_401(customer: Customer | None) -> Customer:
    if not customer:
        raise HTTPException(status_code=401, detail='Missing customer login')
    return customer


def _address_or_404(db: Session, customer: Customer, address_id: int) -> CustomerAddress:
    address = (
        db.query(CustomerAddress)
        .filter(CustomerAddress.id == address_id, CustomerAddress.customer_id == customer.id)
        .first()
    )
    if not address:
        raise HTTPException(status_code=404, detail='Address not found')
    return address


def _sync_default_address(db: Session, customer: Customer, address: CustomerAddress) -> None:
    if address.is_default:
        db.query(CustomerAddress).filter(
            CustomerAddress.customer_id == customer.id,
            CustomerAddress.id != address.id,
        ).update({CustomerAddress.is_default: False})


def _apply_address_payload(address: CustomerAddress, payload: CustomerAddressUpsert) -> None:
    address.receiver_name = payload.receiver_name
    address.receiver_phone = payload.receiver_phone
    address.province = payload.province
    address.city = payload.city
    address.district = payload.district
    address.detail_address = payload.detail_address
    address.delivery_note = payload.delivery_note
    address.is_default = payload.is_default
    address.latitude = payload.latitude
    address.longitude = payload.longitude


@router.get('/categories', response_model=list[FruitCategoryOut])
def list_categories(db: Session = Depends(get_db)):
    return (
        db.query(FruitCategory)
        .filter(FruitCategory.is_active.is_(True))
        .order_by(FruitCategory.sort_order.asc(), FruitCategory.id.asc())
        .all()
    )


@router.get('/fruits', response_model=list[FruitOut])
def list_fruits(category: str | None = None, keyword: str | None = None, db: Session = Depends(get_db)):
    query = db.query(Fruit).options(joinedload(Fruit.quote), joinedload(Fruit.category_ref)).order_by(Fruit.is_recommended.desc(), Fruit.id.desc())
    if category:
        query = query.filter(Fruit.category == category)
    if keyword:
        query = query.filter(Fruit.name.like(f'%{keyword}%'))
    return query.all()


@router.get('/fruits/{fruit_id}', response_model=FruitOut)
def get_fruit(fruit_id: int, db: Session = Depends(get_db)):
    fruit = db.query(Fruit).options(joinedload(Fruit.quote), joinedload(Fruit.category_ref)).filter(Fruit.id == fruit_id).first()
    if not fruit:
        raise HTTPException(status_code=404, detail='Fruit not found')
    return fruit


@router.get('/customers/me', response_model=CustomerOut)
def get_me(
    phone: str | None = None,
    db: Session = Depends(get_db),
    auth_customer: Customer | None = Depends(get_optional_auth_customer),
):
    if auth_customer:
        return auth_customer
    if phone:
        customer = db.query(Customer).filter(Customer.phone == phone).first()
        if customer:
            return customer
    raise HTTPException(status_code=401, detail='Missing customer login')


@router.patch('/customers/me', response_model=CustomerOut)
def update_me(
    payload: CustomerProfileUpdate,
    db: Session = Depends(get_db),
    auth_customer: Customer | None = Depends(get_optional_auth_customer),
):
    if not auth_customer:
        raise HTTPException(status_code=401, detail='Missing customer login')
    if payload.nickname is not None:
        auth_customer.nickname = payload.nickname
    if payload.avatar_url is not None:
        auth_customer.avatar_url = payload.avatar_url
    if payload.contact_name is not None:
        auth_customer.contact_name = payload.contact_name
    if payload.phone:
        auth_customer = _attach_phone_to_customer(db, auth_customer, payload.phone)
    db.commit()
    db.refresh(auth_customer)
    return auth_customer


@router.get('/addresses', response_model=list[CustomerAddressOut])
def list_addresses(
    db: Session = Depends(get_db),
    auth_customer: Customer | None = Depends(get_optional_auth_customer),
):
    customer = _current_customer_or_401(auth_customer)
    return (
        db.query(CustomerAddress)
        .filter(CustomerAddress.customer_id == customer.id)
        .order_by(CustomerAddress.is_default.desc(), CustomerAddress.id.desc())
        .all()
    )


@router.post('/addresses', response_model=CustomerAddressOut, status_code=status.HTTP_201_CREATED)
def create_address(
    payload: CustomerAddressUpsert,
    db: Session = Depends(get_db),
    auth_customer: Customer | None = Depends(get_optional_auth_customer),
):
    customer = _current_customer_or_401(auth_customer)
    has_address = db.query(CustomerAddress).filter(CustomerAddress.customer_id == customer.id).first()
    address = CustomerAddress(customer_id=customer.id)
    _apply_address_payload(address, payload)
    if not has_address:
        address.is_default = True
    db.add(address)
    db.flush()
    _sync_default_address(db, customer, address)
    db.commit()
    db.refresh(address)
    return address


@router.patch('/addresses/{address_id}', response_model=CustomerAddressOut)
def update_address(
    address_id: int,
    payload: CustomerAddressUpsert,
    db: Session = Depends(get_db),
    auth_customer: Customer | None = Depends(get_optional_auth_customer),
):
    customer = _current_customer_or_401(auth_customer)
    address = _address_or_404(db, customer, address_id)
    _apply_address_payload(address, payload)
    _sync_default_address(db, customer, address)
    db.commit()
    db.refresh(address)
    return address


@router.delete('/addresses/{address_id}')
def delete_address(
    address_id: int,
    db: Session = Depends(get_db),
    auth_customer: Customer | None = Depends(get_optional_auth_customer),
):
    customer = _current_customer_or_401(auth_customer)
    address = _address_or_404(db, customer, address_id)
    was_default = address.is_default
    db.delete(address)
    db.flush()
    if was_default:
        next_address = (
            db.query(CustomerAddress)
            .filter(CustomerAddress.customer_id == customer.id)
            .order_by(CustomerAddress.id.desc())
            .first()
        )
        if next_address:
            next_address.is_default = True
    db.commit()
    return {'ok': True}


def _attach_phone_to_customer(db: Session, customer: Customer, phone: str) -> Customer:
    existing = db.query(Customer).filter(Customer.phone == phone, Customer.id != customer.id).first()
    if existing and not existing.wechat_openid:
        # Merge old phone-only records into the logged-in WeChat customer.
        db.query(CustomerVerification).filter(CustomerVerification.customer_id == existing.id).update({
            CustomerVerification.customer_id: customer.id,
        })
        db.query(Order).filter(Order.customer_id == existing.id).update({Order.customer_id: customer.id})
        if existing.shop_name and not customer.shop_name:
            customer.shop_name = existing.shop_name
        if existing.contact_name and not customer.contact_name:
            customer.contact_name = existing.contact_name
        if existing.business_type and not customer.business_type:
            customer.business_type = existing.business_type
        if existing.verification_status != 'unverified':
            customer.verification_status = existing.verification_status
        db.delete(existing)
        db.flush()
    elif existing:
        raise HTTPException(status_code=409, detail='Phone number is already bound')
    customer.phone = phone
    return customer


@router.get('/customers/verification/me', response_model=VerificationOut)
def get_my_verification(
    db: Session = Depends(get_db),
    auth_customer: Customer | None = Depends(get_optional_auth_customer),
):
    customer = _current_customer_or_401(auth_customer)
    verification = (
        db.query(CustomerVerification)
        .filter(CustomerVerification.customer_id == customer.id)
        .order_by(CustomerVerification.id.desc())
        .first()
    )
    if not verification:
        raise HTTPException(status_code=404, detail='Verification not found')
    return _verification_payload(verification)


@router.post('/customers/avatar', response_model=CustomerOut)
async def upload_customer_avatar(
    avatar: UploadFile = File(...),
    db: Session = Depends(get_db),
    auth_customer: Customer | None = Depends(get_optional_auth_customer),
):
    customer = _current_customer_or_401(auth_customer)
    avatar_url = await save_upload(avatar, 'customer-avatars')
    customer.avatar_url = avatar_url
    db.commit()
    db.refresh(customer)
    return customer


@router.post('/customers/verification')
async def submit_verification(
    phone: str = Form(...),
    shop_name: str = Form(...),
    contact_name: str = Form(...),
    business_type: str = Form(...),
    wechat_openid: str | None = Form(default=None),
    images: list[UploadFile] = File(...),
    db: Session = Depends(get_db),
    auth_customer: Customer | None = Depends(get_optional_auth_customer),
):
    if auth_customer:
        customer = _attach_phone_to_customer(db, auth_customer, phone)
    else:
        customer = get_or_create_customer(db, phone=phone, wechat_openid=wechat_openid)
    pending_verification = (
        db.query(CustomerVerification)
        .filter(
            CustomerVerification.customer_id == customer.id,
            CustomerVerification.status == 'pending_review',
        )
        .first()
    )
    if pending_verification or customer.verification_status == 'pending_review':
        raise HTTPException(status_code=400, detail='认证审核中，请勿重复提交')
    image_urls = [await save_upload(image, 'customer-verifications') for image in images]

    verification = CustomerVerification(
        customer_id=customer.id,
        shop_name=shop_name,
        contact_name=contact_name,
        phone=phone,
        business_type=business_type,
        image_urls=json.dumps(image_urls, ensure_ascii=False),
        status='pending_review',
    )
    if customer.verification_status != 'verified':
        customer.verification_status = 'pending_review'
        customer.shop_name = shop_name
        customer.contact_name = contact_name
        customer.business_type = business_type
    db.add(verification)
    db.commit()
    db.refresh(verification)
    return _verification_payload(verification)


@router.post('/orders', response_model=OrderOut, status_code=status.HTTP_201_CREATED)
async def create_order(
    payload: OrderCreate,
    db: Session = Depends(get_db),
    auth_customer: Customer | None = Depends(get_optional_auth_customer),
):
    customer = auth_customer or get_or_create_customer(db, phone=payload.customer_phone, wechat_openid=payload.wechat_openid)
    order = Order(
        order_no=_order_no(),
        customer_id=customer.id,
        status='pending',
        receiver_name=payload.receiver_name,
        receiver_phone=payload.receiver_phone,
        province=payload.province,
        city=payload.city,
        district=payload.district,
        detail_address=payload.detail_address,
        delivery_note=payload.delivery_note,
    )
    _apply_order_payload(order, customer, payload, db)
    db.add(order)
    db.commit()
    db.refresh(order)

    try:
        await send_order_email(order)
        order.email_notify_status = 'sent'
    except Exception:
        order.email_notify_status = 'failed'
    db.commit()
    db.refresh(order)
    return order


@router.get('/orders/detail/{order_id}', response_model=OrderOut)
def get_order(
    order_id: int,
    db: Session = Depends(get_db),
    auth_customer: Customer | None = Depends(get_optional_auth_customer),
):
    if not auth_customer:
        raise HTTPException(status_code=401, detail='Missing customer login')
    order = (
        db.query(Order)
        .options(joinedload(Order.items).joinedload(OrderItem.fruit))
        .filter(Order.id == order_id, Order.customer_id == auth_customer.id)
        .first()
    )
    if not order:
        raise HTTPException(status_code=404, detail='Order not found')
    return order


@router.patch('/orders/{order_id}', response_model=OrderOut)
def update_order(
    order_id: int,
    payload: OrderCreate,
    db: Session = Depends(get_db),
    auth_customer: Customer | None = Depends(get_optional_auth_customer),
):
    if not auth_customer:
        raise HTTPException(status_code=401, detail='Missing customer login')
    order = (
        db.query(Order)
        .options(joinedload(Order.items).joinedload(OrderItem.fruit))
        .filter(Order.id == order_id, Order.customer_id == auth_customer.id)
        .first()
    )
    if not order:
        raise HTTPException(status_code=404, detail='Order not found')
    _assert_order_editable(order)
    _apply_order_payload(order, auth_customer, payload, db)
    db.commit()
    db.refresh(order)
    return order


@router.get('/orders/my', response_model=list[OrderOut])
def my_orders(
    phone: str | None = None,
    db: Session = Depends(get_db),
    auth_customer: Customer | None = Depends(get_optional_auth_customer),
):
    if auth_customer:
        customer_id = auth_customer.id
    elif phone:
        customer = db.query(CustomerVerification).filter(CustomerVerification.phone == phone).first()
        db_customer = db.query(Customer).filter(Customer.phone == phone).first()
        if not db_customer and not customer:
            return []
        customer_id = db_customer.id if db_customer else customer.customer_id
    else:
        return []
    return (
        db.query(Order)
        .options(joinedload(Order.items).joinedload(OrderItem.fruit))
        .filter(Order.customer_id == customer_id)
        .order_by(Order.id.desc())
        .all()
    )
