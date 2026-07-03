import json
from collections import defaultdict
from datetime import date, datetime, time, timedelta
from decimal import Decimal

from fastapi import APIRouter, Depends, File, HTTPException, Query, UploadFile
from sqlalchemy import func as sa_func
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session, joinedload

from app.api.deps import admin_permissions, get_current_admin, get_optional_auth_customer, require_admin_permission
from app.core.security import create_access_token, hash_password, verify_password
from app.db.session import get_db
from app.models import Admin, Customer, CustomerVerification, Fruit, FruitCategory, Order, PriceQuote
from app.schemas import AdminAuthOut, AdminEntryVisibleOut, AdminLogin, AdminOut, AdminPasswordUpdate, AdminUpsert, CustomerAdminOut, FruitCategoryOut, FruitCategoryUpsert, FruitOut, FruitUpsert, OrderBulkStatusUpdate, OrderOut, OrderStatusUpdate, SalesStatsOut, VerificationReview
from app.services.upload import save_upload, to_public_url, to_public_urls, to_storage_path, to_storage_paths

router = APIRouter(prefix='/admin')


def _admin_payload(admin: Admin) -> AdminOut:
    return AdminOut.model_validate(admin)


def _assert_not_last_super_admin(db: Session, admin: Admin, next_role: str | None = None, next_active: bool | None = None) -> None:
    will_remain_super = (next_role or admin.role) == 'super_admin' and (admin.is_active if next_active is None else next_active)
    if will_remain_super:
        return
    active_super_count = db.query(Admin).filter(Admin.role == 'super_admin', Admin.is_active.is_(True)).count()
    if admin.role == 'super_admin' and admin.is_active and active_super_count <= 1:
        raise HTTPException(status_code=400, detail='Cannot disable or downgrade the last super admin')


def _apply_admin_payload(admin: Admin, payload: AdminUpsert, db: Session, is_create: bool = False) -> None:
    username = payload.username.strip()
    if not username:
        raise HTTPException(status_code=400, detail='Username is required')
    existing = db.query(Admin).filter(Admin.username == username, Admin.id != (admin.id or 0)).first()
    if existing:
        raise HTTPException(status_code=409, detail='Username already exists')
    if payload.wechat_openid:
        openid_owner = db.query(Admin).filter(Admin.wechat_openid == payload.wechat_openid, Admin.id != (admin.id or 0)).first()
        if openid_owner:
            raise HTTPException(status_code=409, detail='WeChat openid already bound')
    if not is_create:
        _assert_not_last_super_admin(db, admin, payload.role, payload.is_active)
    admin.username = username
    admin.role = payload.role
    admin.wechat_openid = payload.wechat_openid or None
    admin.nickname = payload.nickname or None
    admin.is_active = payload.is_active
    if payload.password:
        admin.password_hash = hash_password(payload.password)


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


def _category_or_404(category_id: int, db: Session) -> FruitCategory:
    category = db.query(FruitCategory).filter(FruitCategory.id == category_id).first()
    if not category:
        raise HTTPException(status_code=404, detail='Category not found')
    return category


def _commit_or_category_conflict(db: Session) -> None:
    try:
        db.commit()
    except IntegrityError as exc:
        db.rollback()
        raise HTTPException(status_code=409, detail='Category name already exists') from exc


def _clean_category_icon(icon: str | None) -> str | None:
    value = (icon or '').strip()
    return value[:64] or None


@router.post('/login', response_model=AdminAuthOut)
def login(payload: AdminLogin, db: Session = Depends(get_db)):
    admin = db.query(Admin).filter(Admin.username == payload.username, Admin.is_active.is_(True)).first()
    if not admin or not verify_password(payload.password, admin.password_hash):
        raise HTTPException(status_code=401, detail='Invalid username or password')
    return AdminAuthOut(
        access_token=create_access_token(admin.username),
        admin=_admin_payload(admin),
        permissions=admin_permissions(admin),
    )


@router.get('/me', response_model=AdminAuthOut)
def get_admin_me(admin: Admin = Depends(get_current_admin)):
    return AdminAuthOut(
        access_token='',
        admin=_admin_payload(admin),
        permissions=admin_permissions(admin),
    )


@router.get('/entry-visible', response_model=AdminEntryVisibleOut)
def admin_entry_visible(
    auth_customer: Customer | None = Depends(get_optional_auth_customer),
    db: Session = Depends(get_db),
):
    if not auth_customer or not auth_customer.wechat_openid:
        return AdminEntryVisibleOut(visible=False)
    admin = db.query(Admin).filter(
        Admin.wechat_openid == auth_customer.wechat_openid,
        Admin.is_active.is_(True),
    ).first()
    return AdminEntryVisibleOut(visible=bool(admin))


@router.post('/uploads')
async def upload_admin_image(
    file: UploadFile = File(...),
    _: Admin = Depends(require_admin_permission('fruits')),
):
    path = await save_upload(file, 'fruit-images')
    return {'url': to_public_url(path), 'path': path}


@router.get('/orders', response_model=list[OrderOut])
def list_orders(
    status: str | None = None,
    target_date: date | None = Query(default=None, alias='date'),
    db: Session = Depends(get_db),
    _: Admin = Depends(require_admin_permission('orders')),
):
    query = db.query(Order).options(joinedload(Order.items)).order_by(Order.id.desc())
    if target_date:
        start_at = datetime.combine(target_date, time.min)
        end_at = start_at + timedelta(days=1)
        query = query.filter(Order.created_at >= start_at, Order.created_at < end_at)
    if status:
        query = query.filter(Order.status == status)
    return query.all()


@router.get('/sales-stats', response_model=SalesStatsOut)
def sales_stats(
    target_date: date = Query(default_factory=date.today, alias='date'),
    db: Session = Depends(get_db),
    _: Admin = Depends(require_admin_permission('stats')),
):
    start_at = datetime.combine(target_date, time.min)
    end_at = start_at + timedelta(days=1)
    orders = (
        db.query(Order)
        .options(joinedload(Order.items))
        .filter(Order.created_at >= start_at, Order.created_at < end_at)
        .order_by(Order.id.asc())
        .all()
    )

    counted_orders = [order for order in orders if order.status != 'cancelled']
    item_map = {}
    status_map = defaultdict(lambda: {'order_count': 0, 'amount': Decimal('0')})
    total_quantity = Decimal('0')
    estimated_total = Decimal('0')

    for order in orders:
        status_map[order.status]['order_count'] += 1
        status_map[order.status]['amount'] += order.estimated_total or Decimal('0')

    for order in counted_orders:
        estimated_total += order.estimated_total or Decimal('0')
        for item in order.items:
            key = (item.fruit_id, item.spec, item.unit)
            if key not in item_map:
                item_map[key] = {
                    'fruit_id': item.fruit_id,
                    'fruit_name': item.fruit_name,
                    'spec': item.spec,
                    'unit': item.unit,
                    'quantity': Decimal('0'),
                    'subtotal': Decimal('0'),
                    'order_ids': set(),
                }
            item_map[key]['quantity'] += item.quantity or Decimal('0')
            item_map[key]['subtotal'] += item.subtotal or Decimal('0')
            item_map[key]['order_ids'].add(order.id)
            total_quantity += item.quantity or Decimal('0')

    items = [
        {
            'fruit_id': item['fruit_id'],
            'fruit_name': item['fruit_name'],
            'spec': item['spec'],
            'unit': item['unit'],
            'quantity': item['quantity'],
            'subtotal': item['subtotal'],
            'order_count': len(item['order_ids']),
        }
        for item in item_map.values()
    ]
    items.sort(key=lambda item: item['subtotal'], reverse=True)

    return {
        'date': target_date.isoformat(),
        'order_count': len(counted_orders),
        'item_kind_count': len(item_map),
        'total_quantity': total_quantity,
        'estimated_total': estimated_total,
        'items': items,
        'statuses': [
            {'status': status, 'order_count': data['order_count'], 'amount': data['amount']}
            for status, data in status_map.items()
        ],
    }


@router.get('/delivery-sheet', response_model=list[OrderOut])
def delivery_sheet(
    target_date: date | None = Query(default=None, alias='date'),
    db: Session = Depends(get_db),
    _: Admin = Depends(require_admin_permission('orders')),
):
    query = (
        db.query(Order)
        .options(joinedload(Order.items))
        .filter(Order.status.in_(['pending', 'confirmed', 'delivering']))
        .order_by(Order.created_at.asc(), Order.id.asc())
    )
    if target_date:
        start_at = datetime.combine(target_date, time.min)
        end_at = start_at + timedelta(days=1)
        query = query.filter(Order.created_at >= start_at, Order.created_at < end_at)
    return query.all()


@router.patch('/orders/bulk-status', response_model=list[OrderOut])
def bulk_update_order_status(
    payload: OrderBulkStatusUpdate,
    db: Session = Depends(get_db),
    _: Admin = Depends(require_admin_permission('orders')),
):
    orders = (
        db.query(Order)
        .options(joinedload(Order.items))
        .filter(Order.id.in_(payload.order_ids))
        .all()
    )
    found_ids = {order.id for order in orders}
    missing_ids = [order_id for order_id in payload.order_ids if order_id not in found_ids]
    if missing_ids:
        raise HTTPException(status_code=404, detail=f'Orders not found: {missing_ids}')
    for order in orders:
        order.status = payload.status
    db.commit()
    for order in orders:
        db.refresh(order)
    return sorted(orders, key=lambda item: payload.order_ids.index(item.id))


@router.patch('/orders/{order_id}', response_model=OrderOut)
def update_order_status(
    order_id: int,
    payload: OrderStatusUpdate,
    db: Session = Depends(get_db),
    _: Admin = Depends(require_admin_permission('orders')),
):
    order = db.query(Order).options(joinedload(Order.items)).filter(Order.id == order_id).first()
    if not order:
        raise HTTPException(status_code=404, detail='Order not found')
    order.status = payload.status
    db.commit()
    db.refresh(order)
    return order


@router.get('/verifications')
def list_verifications(
    status: str | None = None,
    db: Session = Depends(get_db),
    _: Admin = Depends(require_admin_permission('verifications')),
):
    query = db.query(CustomerVerification).order_by(CustomerVerification.id.desc())
    if status:
        query = query.filter(CustomerVerification.status == status)
    return [_verification_payload(item) for item in query.all()]


@router.get('/categories', response_model=list[FruitCategoryOut])
def list_admin_categories(
    db: Session = Depends(get_db),
    _: Admin = Depends(require_admin_permission('fruits')),
):
    return db.query(FruitCategory).order_by(FruitCategory.sort_order.asc(), FruitCategory.id.asc()).all()


@router.post('/categories', response_model=FruitCategoryOut)
def create_category(
    payload: FruitCategoryUpsert,
    db: Session = Depends(get_db),
    _: Admin = Depends(require_admin_permission('fruits')),
):
    category = FruitCategory(
        name=payload.name.strip(),
        icon=_clean_category_icon(payload.icon),
        icon_url=to_storage_path(payload.icon_url),
        sort_order=payload.sort_order,
        is_active=payload.is_active,
    )
    if not category.name:
        raise HTTPException(status_code=400, detail='Category name is required')
    db.add(category)
    _commit_or_category_conflict(db)
    db.refresh(category)
    return category


@router.patch('/categories/{category_id}', response_model=FruitCategoryOut)
def update_category(
    category_id: int,
    payload: FruitCategoryUpsert,
    db: Session = Depends(get_db),
    _: Admin = Depends(require_admin_permission('fruits')),
):
    category = _category_or_404(category_id, db)
    next_name = payload.name.strip()
    if not next_name:
        raise HTTPException(status_code=400, detail='Category name is required')
    category.name = next_name
    category.icon = _clean_category_icon(payload.icon)
    category.icon_url = to_storage_path(payload.icon_url)
    category.sort_order = payload.sort_order
    category.is_active = payload.is_active
    for fruit in category.fruits:
        fruit.category = category.name
    _commit_or_category_conflict(db)
    db.refresh(category)
    return category


@router.patch('/verifications/{verification_id}')
def review_verification(
    verification_id: int,
    payload: VerificationReview,
    db: Session = Depends(get_db),
    _: Admin = Depends(require_admin_permission('verifications')),
):
    verification = db.query(CustomerVerification).filter(CustomerVerification.id == verification_id).first()
    if not verification:
        raise HTTPException(status_code=404, detail='Verification not found')

    verification.status = payload.status
    verification.review_note = payload.review_note
    customer = db.query(Customer).filter(Customer.id == verification.customer_id).first()
    if customer:
        if payload.status == 'verified':
            customer.verification_status = 'verified'
            customer.shop_name = verification.shop_name
            customer.contact_name = verification.contact_name
            customer.business_type = verification.business_type
        elif customer.verification_status != 'verified':
            customer.verification_status = 'rejected'
    db.commit()
    db.refresh(verification)
    return _verification_payload(verification)


@router.post('/fruits', response_model=FruitOut)
def create_fruit(
    payload: FruitUpsert,
    db: Session = Depends(get_db),
    _: Admin = Depends(require_admin_permission('fruits')),
):
    category = _category_or_404(payload.category_id, db)
    image_urls = to_storage_paths(payload.image_urls or ([payload.image_url] if payload.image_url else []))
    cover_url = to_storage_path(payload.image_url) or (image_urls[0] if image_urls else None)
    fruit = Fruit(
        name=payload.name,
        category_id=category.id,
        category=category.name,
        image_url=cover_url,
        origin=payload.origin,
        spec=payload.spec,
        unit=payload.unit,
        stock_status=payload.stock_status,
        is_recommended=payload.is_recommended,
    )
    fruit.image_urls = image_urls
    fruit.detail_image_urls = to_storage_paths(payload.detail_image_urls)
    fruit.quote = PriceQuote(
        normal_price=payload.normal_price,
        verified_price=payload.verified_price,
        grade=payload.grade,
        min_order_quantity=payload.min_order_quantity,
        note=payload.note,
    )
    db.add(fruit)
    db.commit()
    db.refresh(fruit)
    return fruit


@router.patch('/fruits/{fruit_id}', response_model=FruitOut)
def update_fruit(
    fruit_id: int,
    payload: FruitUpsert,
    db: Session = Depends(get_db),
    _: Admin = Depends(require_admin_permission('fruits')),
):
    category = _category_or_404(payload.category_id, db)
    fruit = db.query(Fruit).options(joinedload(Fruit.quote), joinedload(Fruit.category_ref)).filter(Fruit.id == fruit_id).first()
    if not fruit:
        raise HTTPException(status_code=404, detail='Fruit not found')

    fruit.name = payload.name
    fruit.category_id = category.id
    fruit.category = category.name
    image_urls = to_storage_paths(payload.image_urls or ([payload.image_url] if payload.image_url else []))
    fruit.image_url = to_storage_path(payload.image_url) or (image_urls[0] if image_urls else None)
    fruit.image_urls = image_urls
    fruit.detail_image_urls = to_storage_paths(payload.detail_image_urls)
    fruit.origin = payload.origin
    fruit.spec = payload.spec
    fruit.unit = payload.unit
    fruit.stock_status = payload.stock_status
    fruit.is_recommended = payload.is_recommended
    if fruit.quote is None:
        fruit.quote = PriceQuote(fruit_id=fruit.id)
    fruit.quote.normal_price = payload.normal_price
    fruit.quote.verified_price = payload.verified_price
    fruit.quote.grade = payload.grade
    fruit.quote.min_order_quantity = payload.min_order_quantity
    fruit.quote.note = payload.note
    db.commit()
    db.refresh(fruit)
    return fruit


@router.get('/admin-users', response_model=list[AdminOut])
def list_admin_users(
    db: Session = Depends(get_db),
    _: Admin = Depends(require_admin_permission('users')),
):
    return db.query(Admin).order_by(Admin.id.asc()).all()


@router.post('/admin-users', response_model=AdminOut)
def create_admin_user(
    payload: AdminUpsert,
    db: Session = Depends(get_db),
    _: Admin = Depends(require_admin_permission('users')),
):
    if not payload.password:
        raise HTTPException(status_code=400, detail='Password is required')
    admin = Admin(username=payload.username.strip(), password_hash=hash_password(payload.password))
    _apply_admin_payload(admin, payload, db, is_create=True)
    db.add(admin)
    db.commit()
    db.refresh(admin)
    return admin


@router.patch('/admin-users/{admin_id}/password', response_model=AdminOut)
def reset_admin_password(
    admin_id: int,
    payload: AdminPasswordUpdate,
    db: Session = Depends(get_db),
    _: Admin = Depends(require_admin_permission('users')),
):
    admin = db.query(Admin).filter(Admin.id == admin_id).first()
    if not admin:
        raise HTTPException(status_code=404, detail='Admin not found')
    admin.password_hash = hash_password(payload.password)
    db.commit()
    db.refresh(admin)
    return admin


@router.patch('/admin-users/{admin_id}', response_model=AdminOut)
def update_admin_user(
    admin_id: int,
    payload: AdminUpsert,
    db: Session = Depends(get_db),
    _: Admin = Depends(require_admin_permission('users')),
):
    admin = db.query(Admin).filter(Admin.id == admin_id).first()
    if not admin:
        raise HTTPException(status_code=404, detail='Admin not found')
    _apply_admin_payload(admin, payload, db)
    db.commit()
    db.refresh(admin)
    return admin


@router.get('/customers', response_model=list[CustomerAdminOut])
def list_customers(
    db: Session = Depends(get_db),
    _: Admin = Depends(require_admin_permission('users')),
):
    rows = (
        db.query(
            Customer,
            sa_func.count(Order.id).label('order_count'),
            sa_func.max(Order.created_at).label('latest_order_at'),
        )
        .outerjoin(Order, Order.customer_id == Customer.id)
        .group_by(Customer.id)
        .order_by(Customer.id.desc())
        .all()
    )
    return [
        CustomerAdminOut(
            id=customer.id,
            phone=customer.phone,
            wechat_openid=customer.wechat_openid,
            nickname=customer.nickname,
            avatar_url=customer.avatar_url,
            verification_status=customer.verification_status,
            shop_name=customer.shop_name,
            contact_name=customer.contact_name,
            business_type=customer.business_type,
            created_at=customer.created_at,
            order_count=order_count or 0,
            latest_order_at=latest_order_at,
        )
        for customer, order_count, latest_order_at in rows
    ]
