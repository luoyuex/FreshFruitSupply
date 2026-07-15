import json
from datetime import datetime, time
from decimal import Decimal

from fastapi import APIRouter, Depends, File, Form, HTTPException, Request, UploadFile, status
from sqlalchemy.orm import Session, joinedload

from app.api.deps import get_current_customer, get_optional_auth_customer
from app.db.session import get_db
from app.models import Announcement, Customer, CustomerAddress, CustomerCoupon, CustomerVerification, Fruit, FruitCategory, Order, OrderItem, OrderPayment
from app.models.domain import CHINA_TZ
from app.schemas import AnnouncementFeedOut, AnnouncementOut, AnnouncementReadOut, CustomerAddressOut, CustomerAddressUpsert, CustomerCouponOut, CustomerOut, CustomerProfileUpdate, DeliveryConfigOut, FruitCategoryOut, FruitOut, MockPaySuccessIn, OrderCreate, OrderEditResult, OrderOut, PaymentParams, PayResponse, VerificationOut
from app.services.coupon import attach_reissue_coupons, compute_discount, effective_coupon_status, grant_coupons_on_verified, release_order_coupons
from app.services.customer import get_or_create_customer
from app.services.settings import compute_delivery_fee, get_delivery_config
from app.services.email import send_order_email
from app.services.upload import save_upload, to_public_urls
from app.services.wechatpay import create_jsapi_payment, generate_out_trade_no, is_mock, verify_and_parse_notify
from app.services.order_maintenance import cancel_order

router = APIRouter()
ORDER_EDIT_CUTOFF = time(22, 30)
EDITABLE_ORDER_STATUSES = {'pending', 'confirmed'}


def _is_before_order_edit_cutoff() -> bool:
    return datetime.now(CHINA_TZ).time() < ORDER_EDIT_CUTOFF


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
    _apply_coupon(order, customer, payload.coupon_id, db)
    _apply_reissue_coupons(order, customer, payload.reissue_coupon_ids, db)
    _apply_delivery_fee(order, db)


def _apply_delivery_fee(order: Order, db: Session) -> None:
    """按后台配置的包邮门槛/配送费，给订单加配送费并计入实付。

    配送费按商品原价合计判断门槛（不扣券），作为独立一行叠加在券后实付之上。
    须在 _apply_coupon 之后调用（依赖其算好的 payable_total）。
    """
    threshold, fee = get_delivery_config(db)
    delivery_fee = compute_delivery_fee(order.estimated_total, threshold, fee)
    order.delivery_fee = delivery_fee
    order.payable_total = order.payable_total + delivery_fee


def _apply_coupon(order: Order, customer: Customer, coupon_id: int | None, db: Session) -> None:
    now = datetime.now()

    # 编辑场景：释放订单原先占用、且与本次不同的券
    if order.coupon_id and order.coupon_id != coupon_id:
        previous = db.query(CustomerCoupon).filter(CustomerCoupon.id == order.coupon_id).first()
        if previous and previous.status == 'used' and previous.order_id == order.id:
            previous.status = 'unused'
            previous.used_at = None
            previous.order_id = None
        order.coupon_id = None

    if not coupon_id:
        order.coupon_id = None
        order.discount_amount = Decimal('0')
        order.payable_total = order.estimated_total
        return

    coupon = (
        db.query(CustomerCoupon)
        .filter(CustomerCoupon.id == coupon_id, CustomerCoupon.customer_id == customer.id)
        .first()
    )
    if not coupon:
        raise HTTPException(status_code=400, detail='优惠券不存在或不属于当前账号')
    # 满减券入口只接满减券；补送券走 reissue_coupon_ids，避免误把补送券当抵扣券
    if coupon.kind != 'discount':
        raise HTTPException(status_code=400, detail='该券不能作为抵扣券使用')
    # 允许编辑时重复提交本订单已占用的同一张券
    reused_on_this_order = coupon.status == 'used' and order.id is not None and coupon.order_id == order.id
    if coupon.status != 'unused' and not reused_on_this_order:
        raise HTTPException(status_code=400, detail='优惠券已被使用')
    if coupon.expires_at < now:
        raise HTTPException(status_code=400, detail='优惠券已过期')
    if order.estimated_total < Decimal(coupon.min_spend or 0):
        raise HTTPException(status_code=400, detail='订单金额未达到优惠券使用门槛')

    discount = compute_discount(coupon, order.estimated_total)
    payable = order.estimated_total - discount
    order.coupon_id = coupon.id
    order.discount_amount = discount
    order.payable_total = payable if payable > 0 else Decimal('0')
    coupon.status = 'used'
    coupon.used_at = now
    # 新建订单此时尚未落库，flush 拿到 order.id 以回写券的 order_id
    if order not in db:
        db.add(order)
    db.flush()
    coupon.order_id = order.id


def _apply_reissue_coupons(order: Order, customer: Customer, coupon_ids: list[int], db: Session) -> None:
    """挂载商品补送券：可叠加多张，无金额/门槛，不影响实付，仅作配货标记。

    与满减券互不干扰。编辑时先释放本订单原先占用、且本次未再选中的补送券。
    """
    now = datetime.now()
    wanted_ids = list(dict.fromkeys(coupon_ids or []))  # 去重且保序

    # 编辑场景：释放本订单原先占用、且本次不再选中的补送券
    previously_used = (
        db.query(CustomerCoupon)
        .filter(
            CustomerCoupon.order_id == order.id,
            CustomerCoupon.kind == 'reissue',
        )
        .all()
        if order.id is not None
        else []
    )
    for coupon in previously_used:
        if coupon.id not in wanted_ids:
            coupon.status = 'unused'
            coupon.used_at = None
            coupon.order_id = None

    if not wanted_ids:
        return

    # 落库拿到 order.id 以回写券的 order_id（新建订单此时尚未 flush）
    if order not in db:
        db.add(order)
    db.flush()

    for coupon_id in wanted_ids:
        coupon = (
            db.query(CustomerCoupon)
            .filter(CustomerCoupon.id == coupon_id, CustomerCoupon.customer_id == customer.id)
            .first()
        )
        if not coupon:
            raise HTTPException(status_code=400, detail='补送券不存在或不属于当前账号')
        if coupon.kind != 'reissue':
            raise HTTPException(status_code=400, detail='该券不是补送券')
        reused_on_this_order = coupon.status == 'used' and coupon.order_id == order.id
        if coupon.status != 'unused' and not reused_on_this_order:
            raise HTTPException(status_code=400, detail='补送券已被使用')
        if coupon.expires_at < now:
            raise HTTPException(status_code=400, detail='补送券已过期')
        coupon.status = 'used'
        coupon.used_at = now
        coupon.order_id = order.id


def _order_no() -> str:
    return datetime.now().strftime('F%Y%m%d%H%M%S%f')[:-3]


def _assert_add_only(order: Order, payload: OrderCreate) -> None:
    """已付款订单编辑只允许加商品/加量，不允许减量或删除（付款后减量会导致金额对不上）。

    校验新明细为原明细的超集：原有每个商品仍在，且数量 >= 原数量。
    """
    old_quantities: dict[int, Decimal] = {}
    for item in order.items:
        old_quantities[item.fruit_id] = old_quantities.get(item.fruit_id, Decimal('0')) + Decimal(item.quantity)
    new_quantities: dict[int, Decimal] = {}
    for line in payload.items:
        new_quantities[line.fruit_id] = new_quantities.get(line.fruit_id, Decimal('0')) + Decimal(line.quantity)
    for fruit_id, old_qty in old_quantities.items():
        new_qty = new_quantities.get(fruit_id, Decimal('0'))
        if new_qty < old_qty:
            raise HTTPException(status_code=400, detail='已付款订单只能增加商品或数量，不能减少或删除')


def _preview_payable(order: Order, customer: Customer, payload: OrderCreate, db: Session) -> Decimal:
    """按变更后的明细预算应付金额，但不改动订单本身（用于判断是否需要补差价）。

    口径与 _apply_order_payload 一致：商品原价合计 - 券抵扣，再加配送费。
    编辑只增不减，原订单占用的满减券仍沿用（门槛只会更容易满足）。
    """
    estimated_total = Decimal('0')
    for line in payload.items:
        fruit = db.query(Fruit).options(joinedload(Fruit.quote)).filter(Fruit.id == line.fruit_id).first()
        if not fruit or not fruit.quote:
            raise HTTPException(status_code=404, detail=f'Fruit {line.fruit_id} not found')
        if fruit.stock_status == 'out_of_stock':
            raise HTTPException(status_code=400, detail=f'{fruit.name} is out of stock')
        price = fruit.quote.verified_price if customer.verification_status == 'verified' else fruit.quote.normal_price
        estimated_total += price * line.quantity

    discount = Decimal('0')
    if payload.coupon_id:
        coupon = db.query(CustomerCoupon).filter(CustomerCoupon.id == payload.coupon_id, CustomerCoupon.customer_id == customer.id).first()
        if coupon and coupon.kind == 'discount':
            discount = compute_discount(coupon, estimated_total)
    threshold, fee = get_delivery_config(db)
    delivery_fee = compute_delivery_fee(estimated_total, threshold, fee)
    payable = estimated_total - discount
    return (payable if payable > 0 else Decimal('0')) + delivery_fee


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


@router.get('/settings/delivery', response_model=DeliveryConfigOut)
def get_delivery_settings(db: Session = Depends(get_db)):
    threshold, fee = get_delivery_config(db)
    return DeliveryConfigOut(free_threshold=threshold, fee=fee)


@router.get('/announcements', response_model=AnnouncementFeedOut)
def list_announcements(
    db: Session = Depends(get_db),
    customer: Customer | None = Depends(get_optional_auth_customer),
):
    """启用中的公告（最新在前）。登录时附带该用户已读位与未读数；游客均为 0。"""
    items = db.query(Announcement).filter(Announcement.is_active.is_(True)).order_by(Announcement.id.desc()).all()
    last_read_id = customer.last_read_announcement_id if customer else 0
    unread_count = sum(1 for item in items if item.id > last_read_id) if customer else 0
    return AnnouncementFeedOut(
        items=[AnnouncementOut.model_validate(item) for item in items],
        last_read_id=last_read_id,
        unread_count=unread_count,
    )


@router.post('/announcements/read', response_model=AnnouncementReadOut)
def mark_announcements_read(
    db: Session = Depends(get_db),
    customer: Customer = Depends(get_current_customer),
):
    """把当前用户已读位推进到最新启用公告的 id（无公告则置 0），清除未读。"""
    latest_id = db.query(Announcement.id).filter(Announcement.is_active.is_(True)).order_by(Announcement.id.desc()).limit(1).scalar()
    customer.last_read_announcement_id = latest_id or 0
    db.commit()
    return AnnouncementReadOut(last_read_id=customer.last_read_announcement_id)


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
    if customer.verification_status == 'verified':
        # 合并到已认证的手机号记录时补发认证券（幂等，不会重复发）
        grant_coupons_on_verified(db, customer)
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


async def _notify_order_paid(db: Session, order: Order) -> None:
    """订单付满后通知供应商配货。挂载补送券后发邮件，回写通知状态。

    邮件由「下单即发」移到「支付成功后发」——只有付过款的订单才需要供应商配货。
    """
    # 先挂载补送券，订单邮件才能带上补送商品明细供配货
    attach_reissue_coupons(db, [order])
    try:
        await send_order_email(order)
        order.email_notify_status = 'sent'
    except Exception:
        order.email_notify_status = 'failed'
    db.commit()
    db.refresh(order)
    attach_reissue_coupons(db, [order])


def _new_payment(order: Order, amount: Decimal, kind: str, pending_payload: str | None = None) -> OrderPayment:
    """新建一笔待支付流水（首付/补差价），商户订单号全局唯一。"""
    return OrderPayment(
        order_id=order.id,
        out_trade_no=generate_out_trade_no(),
        kind=kind,
        amount=amount,
        status='pending',
        pending_payload=pending_payload,
    )


def _reusable_pending_payment(db: Session, order: Order, kind: str) -> OrderPayment | None:
    """取该订单同类型仍待支付的流水，避免重复下单时产生多条 pending 流水。"""
    return (
        db.query(OrderPayment)
        .filter(
            OrderPayment.order_id == order.id,
            OrderPayment.kind == kind,
            OrderPayment.status == 'pending',
        )
        .order_by(OrderPayment.id.desc())
        .first()
    )


@router.post('/orders', response_model=OrderOut, status_code=status.HTTP_201_CREATED)
def create_order(
    payload: OrderCreate,
    db: Session = Depends(get_db),
    auth_customer: Customer | None = Depends(get_optional_auth_customer),
):
    """创建待支付订单。此时不发邮件——需支付成功后才通知供应商配货。

    下单即锁定优惠券占位；若超时未支付，关单时会释放。前端拿到订单后立即调
    POST /orders/{id}/pay 拉起微信支付。
    """
    customer = auth_customer or get_or_create_customer(db, phone=payload.customer_phone, wechat_openid=payload.wechat_openid)
    order = Order(
        order_no=_order_no(),
        customer_id=customer.id,
        status='unpaid',
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
    attach_reissue_coupons(db, [order])
    return order


@router.post('/orders/{order_id}/pay', response_model=PayResponse)
def pay_order(
    order_id: int,
    db: Session = Depends(get_db),
    auth_customer: Customer | None = Depends(get_optional_auth_customer),
):
    """为待支付订单发起（或复用）首付支付，返回小程序拉起支付所需参数。"""
    customer = _current_customer_or_401(auth_customer)
    order = (
        db.query(Order)
        .filter(Order.id == order_id, Order.customer_id == customer.id)
        .first()
    )
    if not order:
        raise HTTPException(status_code=404, detail='Order not found')
    if order.status != 'unpaid':
        raise HTTPException(status_code=400, detail='订单无需支付或已支付')

    amount = order.payable_total
    if amount is None or amount <= 0:
        raise HTTPException(status_code=400, detail='订单金额异常，无法支付')

    payment = _reusable_pending_payment(db, order, 'initial')
    if payment is None:
        payment = _new_payment(order, amount, 'initial')
        db.add(payment)
        db.flush()
    elif payment.amount != amount:
        # 复用旧流水前对齐金额（极少见：编辑改动了应付但流水已生成）
        payment.amount = amount

    pay_params = create_jsapi_payment(payment, customer.wechat_openid or '')
    db.commit()
    return PayResponse(
        order_id=order.id,
        out_trade_no=payment.out_trade_no,
        amount=payment.amount,
        pay_params=PaymentParams(out_trade_no=payment.out_trade_no, **pay_params) if 'out_trade_no' not in pay_params else PaymentParams(**pay_params),
    )


async def _settle_successful_payment(db: Session, payment: OrderPayment, transaction_id: str | None) -> None:
    """支付成功后的统一结算：幂等标记流水、累加已付、推进订单状态并通知。

    首付付满 → 订单从 unpaid 转 pending 并发配货邮件；
    补差价付满 → 落库暂存的明细变更（加商品/加量），刷新应付并重发配货邮件。
    """
    if payment.status == 'success':
        return  # 幂等：重复回调直接忽略
    payment.status = 'success'
    payment.transaction_id = transaction_id
    payment.paid_at = datetime.now()

    order = (
        db.query(Order)
        .options(joinedload(Order.items).joinedload(OrderItem.fruit))
        .filter(Order.id == payment.order_id)
        .first()
    )
    if not order:
        db.commit()
        return
    order.paid_amount = (order.paid_amount or Decimal('0')) + payment.amount

    # 首付付满：订单成立，转待确认并通知供应商
    if payment.kind == 'initial' and order.status == 'unpaid' and order.paid_amount >= order.payable_total:
        order.status = 'pending'
        db.commit()
        db.refresh(order)
        await _notify_order_paid(db, order)
        return

    # 补差价付满：把编辑时暂存的明细变更落库，刷新应付后重发配货邮件
    if payment.kind == 'supplement' and payment.pending_payload:
        customer = db.query(Customer).filter(Customer.id == order.customer_id).first()
        stored = OrderCreate(**json.loads(payment.pending_payload))
        _apply_order_payload(order, customer, stored, db)
        # 落库后清空暂存，避免重复应用
        payment.pending_payload = None
        db.commit()
        db.refresh(order)
        await _notify_order_paid(db, order)
        return

    db.commit()


@router.post('/payments/wechat/notify')
async def wechat_pay_notify(request: Request, db: Session = Depends(get_db)):
    """微信支付结果回调：验签解密 → 定位流水 → 结算。返回微信要求的应答格式。"""
    body = await request.body()
    try:
        result = verify_and_parse_notify(dict(request.headers), body)
    except Exception:
        # 验签/解密失败，让微信重试
        return {'code': 'FAIL', 'message': '验签失败'}

    out_trade_no = result.get('out_trade_no')
    trade_state = result.get('trade_state')
    transaction_id = result.get('transaction_id')
    if not out_trade_no:
        return {'code': 'FAIL', 'message': '缺少订单号'}
    payment = db.query(OrderPayment).filter(OrderPayment.out_trade_no == out_trade_no).first()
    if not payment:
        return {'code': 'FAIL', 'message': '流水不存在'}
    if trade_state == 'SUCCESS':
        await _settle_successful_payment(db, payment, transaction_id)
    return {'code': 'SUCCESS', 'message': '成功'}


@router.post('/payments/dev/mock-success', response_model=OrderOut)
async def mock_pay_success(
    payload: MockPaySuccessIn,
    db: Session = Depends(get_db),
    auth_customer: Customer | None = Depends(get_optional_auth_customer),
):
    """仅 Mock 模式：模拟一笔支付成功，驱动与真实回调一致的结算逻辑，便于凭证到位前联调。"""
    if not is_mock():
        raise HTTPException(status_code=403, detail='Mock payment is disabled')
    customer = _current_customer_or_401(auth_customer)
    payment = db.query(OrderPayment).filter(OrderPayment.out_trade_no == payload.out_trade_no).first()
    if not payment:
        raise HTTPException(status_code=404, detail='Payment not found')
    order = db.query(Order).filter(Order.id == payment.order_id, Order.customer_id == customer.id).first()
    if not order:
        raise HTTPException(status_code=404, detail='Order not found')
    await _settle_successful_payment(db, payment, f'mock_txn_{payment.out_trade_no}')
    db.refresh(order)
    attach_reissue_coupons(db, [order])
    return order


@router.post('/orders/{order_id}/cancel', response_model=OrderOut)
def cancel_my_order(
    order_id: int,
    db: Session = Depends(get_db),
    auth_customer: Customer | None = Depends(get_optional_auth_customer),
):
    """用户取消自己的订单。

    已付款订单原路退款并置 cancelled；待支付订单直接关闭。已在配送中/已完成的订单
    不允许自助取消。取消后释放占用的优惠券。
    """
    customer = _current_customer_or_401(auth_customer)
    order = (
        db.query(Order)
        .options(joinedload(Order.items).joinedload(OrderItem.fruit))
        .filter(Order.id == order_id, Order.customer_id == customer.id)
        .first()
    )
    if not order:
        raise HTTPException(status_code=404, detail='Order not found')
    if order.status not in {'unpaid', 'pending', 'confirmed'}:
        raise HTTPException(status_code=400, detail='当前订单状态不可取消')
    cancel_order(db, order)
    db.commit()
    db.refresh(order)
    attach_reissue_coupons(db, [order])
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
    attach_reissue_coupons(db, [order])
    return order


@router.patch('/orders/{order_id}', response_model=OrderEditResult)
def update_order(
    order_id: int,
    payload: OrderCreate,
    db: Session = Depends(get_db),
    auth_customer: Customer | None = Depends(get_optional_auth_customer),
):
    """编辑已付款订单：只能加商品/加量，不能减。

    加量导致应付上升时，不立即改订单，而是把变更暂存进一笔 supplement 待支付流水，
    返回补差价的拉起支付参数；支付成功回调后暂存的变更才落库（暂存式，财务最严谨）。
    应付未上升（如仅改配送备注/收货信息）时，变更直接落库、无需补款。
    """
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
    _assert_add_only(order, payload)

    new_payable = _preview_payable(order, auth_customer, payload, db)
    supplement = new_payable - (order.paid_amount or Decimal('0'))

    # 不需补款：变更直接落库（收货信息/备注变化，或加了免费补送券但应付未上升）
    if supplement <= 0:
        _apply_order_payload(order, auth_customer, payload, db)
        db.commit()
        db.refresh(order)
        attach_reissue_coupons(db, [order])
        return OrderEditResult(need_payment=False, supplement_amount=Decimal('0'), order=OrderOut.model_validate(order))

    # 需补款：把变更暂存到补差价流水，支付成功回调后才落库；订单本身此刻不变
    existing = _reusable_pending_payment(db, order, 'supplement')
    if existing is not None:
        existing.status = 'cancelled'  # 作废上一笔未支付的补差价流水，避免多条 pending 叠加
    pending_payload = payload.model_dump_json()
    payment = _new_payment(order, supplement, 'supplement', pending_payload=pending_payload)
    db.add(payment)
    db.flush()
    pay_params = create_jsapi_payment(payment, auth_customer.wechat_openid or '')
    db.commit()
    db.refresh(order)
    attach_reissue_coupons(db, [order])
    pay = PayResponse(
        order_id=order.id,
        out_trade_no=payment.out_trade_no,
        amount=payment.amount,
        pay_params=PaymentParams(**({'out_trade_no': payment.out_trade_no, **pay_params} if 'out_trade_no' not in pay_params else pay_params)),
    )
    return OrderEditResult(need_payment=True, supplement_amount=supplement, order=OrderOut.model_validate(order), pay=pay)


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
    orders = (
        db.query(Order)
        .options(joinedload(Order.items).joinedload(OrderItem.fruit))
        .filter(Order.customer_id == customer_id)
        .order_by(Order.id.desc())
        .all()
    )
    attach_reissue_coupons(db, orders)
    return orders


@router.get('/coupons/my', response_model=list[CustomerCouponOut])
def my_coupons(
    status: str | None = None,
    db: Session = Depends(get_db),
    auth_customer: Customer | None = Depends(get_optional_auth_customer),
):
    customer = _current_customer_or_401(auth_customer)
    coupons = (
        db.query(CustomerCoupon)
        .filter(CustomerCoupon.customer_id == customer.id)
        .order_by(CustomerCoupon.id.desc())
        .all()
    )
    now = datetime.now()
    result: list[CustomerCouponOut] = []
    for coupon in coupons:
        # 未使用但已过期的券，动态呈现为 expired（不改动库中状态）
        effective_status = effective_coupon_status(coupon, now)
        if status and effective_status != status:
            continue
        data = CustomerCouponOut.model_validate(coupon)
        data.status = effective_status
        result.append(data)
    return result
