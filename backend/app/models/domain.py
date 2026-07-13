import json
from datetime import datetime, time, timedelta, timezone
from decimal import Decimal

from sqlalchemy import Boolean, DateTime, ForeignKey, Integer, Numeric, String, Text, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.session import Base

# 中国大陆固定 UTC+8（无夏令时），用固定偏移避免依赖系统/tzdata 的 IANA 时区库
# （Windows 及精简版 Linux/Docker 镜像常缺 tzdata，ZoneInfo('Asia/Shanghai') 会抛错）
CHINA_TZ = timezone(timedelta(hours=8))


class TimestampMixin:
    created_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.now(), onupdate=func.now())


class Customer(TimestampMixin, Base):
    __tablename__ = 'customers'

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    phone: Mapped[str] = mapped_column(String(32), unique=True, index=True)
    wechat_openid: Mapped[str | None] = mapped_column(String(128), unique=True, nullable=True)
    nickname: Mapped[str | None] = mapped_column(String(80), nullable=True)
    avatar_url: Mapped[str | None] = mapped_column(String(255), nullable=True)
    verification_status: Mapped[str] = mapped_column(String(32), default='unverified', index=True)
    shop_name: Mapped[str | None] = mapped_column(String(120), nullable=True)
    contact_name: Mapped[str | None] = mapped_column(String(60), nullable=True)
    business_type: Mapped[str | None] = mapped_column(String(80), nullable=True)

    verifications: Mapped[list['CustomerVerification']] = relationship(back_populates='customer')
    orders: Mapped[list['Order']] = relationship(back_populates='customer')
    addresses: Mapped[list['CustomerAddress']] = relationship(back_populates='customer', cascade='all, delete-orphan')


class CustomerAddress(TimestampMixin, Base):
    __tablename__ = 'customer_addresses'

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    customer_id: Mapped[int] = mapped_column(ForeignKey('customers.id'), index=True)
    receiver_name: Mapped[str] = mapped_column(String(60))
    receiver_phone: Mapped[str] = mapped_column(String(32))
    province: Mapped[str] = mapped_column(String(60))
    city: Mapped[str] = mapped_column(String(60))
    district: Mapped[str] = mapped_column(String(60))
    detail_address: Mapped[str] = mapped_column(String(255))
    delivery_note: Mapped[str | None] = mapped_column(Text, nullable=True)
    is_default: Mapped[bool] = mapped_column(Boolean, default=False, index=True)
    latitude: Mapped[float | None] = mapped_column(Numeric(10, 7), nullable=True)
    longitude: Mapped[float | None] = mapped_column(Numeric(10, 7), nullable=True)

    customer: Mapped[Customer] = relationship(back_populates='addresses')


class CustomerVerification(TimestampMixin, Base):
    __tablename__ = 'customer_verifications'

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    customer_id: Mapped[int] = mapped_column(ForeignKey('customers.id'), index=True)
    shop_name: Mapped[str] = mapped_column(String(120))
    contact_name: Mapped[str] = mapped_column(String(60))
    phone: Mapped[str] = mapped_column(String(32), index=True)
    business_type: Mapped[str] = mapped_column(String(80))
    image_urls: Mapped[str] = mapped_column(Text)
    status: Mapped[str] = mapped_column(String(32), default='pending_review', index=True)
    review_note: Mapped[str | None] = mapped_column(Text, nullable=True)

    customer: Mapped[Customer] = relationship(back_populates='verifications')


class FruitCategory(TimestampMixin, Base):
    __tablename__ = 'fruit_categories'

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    name: Mapped[str] = mapped_column(String(60), unique=True, index=True)
    icon: Mapped[str | None] = mapped_column(String(64), nullable=True)
    icon_url: Mapped[str | None] = mapped_column(String(255), nullable=True)
    sort_order: Mapped[int] = mapped_column(Integer, default=0, index=True)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, index=True)

    fruits: Mapped[list['Fruit']] = relationship(back_populates='category_ref')


class Fruit(TimestampMixin, Base):
    __tablename__ = 'fruits'

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    name: Mapped[str] = mapped_column(String(80), index=True)
    category_id: Mapped[int | None] = mapped_column(ForeignKey('fruit_categories.id'), nullable=True, index=True)
    category: Mapped[str] = mapped_column(String(60), index=True)
    image_url: Mapped[str | None] = mapped_column(String(255), nullable=True)
    image_urls_json: Mapped[str | None] = mapped_column(Text, nullable=True)
    detail_image_urls_json: Mapped[str | None] = mapped_column(Text, nullable=True)
    origin: Mapped[str | None] = mapped_column(String(120), nullable=True)
    spec: Mapped[str] = mapped_column(String(120))
    unit: Mapped[str] = mapped_column(String(20), default='斤')
    stock_status: Mapped[str] = mapped_column(String(32), default='in_stock', index=True)
    is_recommended: Mapped[bool] = mapped_column(Boolean, default=False)

    @property
    def image_urls(self) -> list[str]:
        if not self.image_urls_json:
            return [self.image_url] if self.image_url else []
        try:
            urls = json.loads(self.image_urls_json)
        except json.JSONDecodeError:
            urls = []
        if self.image_url and self.image_url not in urls:
            urls.insert(0, self.image_url)
        return urls

    @image_urls.setter
    def image_urls(self, urls: list[str] | None) -> None:
        clean_urls = [url for url in (urls or []) if url]
        self.image_urls_json = json.dumps(clean_urls, ensure_ascii=False)
        self.image_url = clean_urls[0] if clean_urls else None

    @property
    def detail_image_urls(self) -> list[str]:
        if not self.detail_image_urls_json:
            return []
        try:
            urls = json.loads(self.detail_image_urls_json)
        except json.JSONDecodeError:
            urls = []
        return [url for url in urls if url]

    @detail_image_urls.setter
    def detail_image_urls(self, urls: list[str] | None) -> None:
        clean_urls = [url for url in (urls or []) if url]
        self.detail_image_urls_json = json.dumps(clean_urls, ensure_ascii=False)

    category_ref: Mapped[FruitCategory | None] = relationship(back_populates='fruits')
    quote: Mapped['PriceQuote'] = relationship(back_populates='fruit', uselist=False, cascade='all, delete-orphan')
    order_items: Mapped[list['OrderItem']] = relationship(back_populates='fruit')


class PriceQuote(TimestampMixin, Base):
    __tablename__ = 'price_quotes'

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    fruit_id: Mapped[int] = mapped_column(ForeignKey('fruits.id'), unique=True, index=True)
    normal_price: Mapped[Decimal] = mapped_column(Numeric(10, 2))
    verified_price: Mapped[Decimal] = mapped_column(Numeric(10, 2))
    grade: Mapped[str] = mapped_column(String(60), default='一级')
    min_order_quantity: Mapped[Decimal] = mapped_column(Numeric(10, 2), default=1)
    note: Mapped[str | None] = mapped_column(Text, nullable=True)

    fruit: Mapped[Fruit] = relationship(back_populates='quote')


class Order(TimestampMixin, Base):
    __tablename__ = 'orders'

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    order_no: Mapped[str] = mapped_column(String(32), unique=True, index=True)
    customer_id: Mapped[int] = mapped_column(ForeignKey('customers.id'), index=True)
    status: Mapped[str] = mapped_column(String(32), default='pending', index=True)
    estimated_total: Mapped[Decimal] = mapped_column(Numeric(12, 2), default=0)
    receiver_name: Mapped[str] = mapped_column(String(60))
    receiver_phone: Mapped[str] = mapped_column(String(32))
    province: Mapped[str] = mapped_column(String(60))
    city: Mapped[str] = mapped_column(String(60))
    district: Mapped[str] = mapped_column(String(60))
    detail_address: Mapped[str] = mapped_column(String(255))
    delivery_note: Mapped[str | None] = mapped_column(Text, nullable=True)
    email_notify_status: Mapped[str] = mapped_column(String(32), default='pending')
    coupon_id: Mapped[int | None] = mapped_column(Integer, nullable=True, index=True)
    discount_amount: Mapped[Decimal] = mapped_column(Numeric(12, 2), default=0)
    delivery_fee: Mapped[Decimal] = mapped_column(Numeric(12, 2), default=0)
    payable_total: Mapped[Decimal] = mapped_column(Numeric(12, 2), default=0)

    customer: Mapped[Customer] = relationship(back_populates='orders')
    items: Mapped[list['OrderItem']] = relationship(back_populates='order', cascade='all, delete-orphan')

    @property
    def can_edit(self) -> bool:
        now = datetime.now(CHINA_TZ).time()
        return self.status in {'pending', 'confirmed'} and now < time(22, 30)


class OrderItem(Base):
    __tablename__ = 'order_items'

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    order_id: Mapped[int] = mapped_column(ForeignKey('orders.id'), index=True)
    fruit_id: Mapped[int] = mapped_column(ForeignKey('fruits.id'), index=True)
    fruit_name: Mapped[str] = mapped_column(String(80))
    spec: Mapped[str] = mapped_column(String(120))
    unit: Mapped[str] = mapped_column(String(20))
    price: Mapped[Decimal] = mapped_column(Numeric(10, 2))
    quantity: Mapped[Decimal] = mapped_column(Numeric(10, 2))
    subtotal: Mapped[Decimal] = mapped_column(Numeric(12, 2))

    order: Mapped[Order] = relationship(back_populates='items')
    fruit: Mapped[Fruit] = relationship(back_populates='order_items')

    @property
    def image_url(self) -> str | None:
        # 订单项本身不存图，封面取自关联水果，便于订单页展示真实缩略图
        return self.fruit.image_url if self.fruit else None


class Admin(TimestampMixin, Base):
    __tablename__ = 'admins'

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    username: Mapped[str] = mapped_column(String(60), unique=True, index=True)
    password_hash: Mapped[str] = mapped_column(String(255))
    role: Mapped[str] = mapped_column(String(32), default='super_admin', index=True)
    wechat_openid: Mapped[str | None] = mapped_column(String(128), unique=True, nullable=True)
    nickname: Mapped[str | None] = mapped_column(String(80), nullable=True)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)


class SystemSetting(TimestampMixin, Base):
    __tablename__ = 'system_settings'

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    key: Mapped[str] = mapped_column(String(80), unique=True, index=True)
    value: Mapped[str] = mapped_column(Text)


class CouponTemplate(TimestampMixin, Base):
    __tablename__ = 'coupon_templates'

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    name: Mapped[str] = mapped_column(String(80))
    description: Mapped[str | None] = mapped_column(Text, nullable=True)
    discount_type: Mapped[str] = mapped_column(String(16), default='amount')  # 预留扩展，本期只用 amount
    amount: Mapped[Decimal] = mapped_column(Numeric(10, 2), default=0)
    min_spend: Mapped[Decimal] = mapped_column(Numeric(12, 2), default=0)  # 满减门槛，0=无门槛
    valid_days: Mapped[int] = mapped_column(Integer, default=30)  # 领取后 N 天到期
    grant_on_verified: Mapped[bool] = mapped_column(Boolean, default=False, index=True)
    per_customer_limit: Mapped[int] = mapped_column(Integer, default=1)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, index=True)


class CustomerCoupon(TimestampMixin, Base):
    __tablename__ = 'customer_coupons'

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    customer_id: Mapped[int] = mapped_column(ForeignKey('customers.id'), index=True)
    template_id: Mapped[int] = mapped_column(ForeignKey('coupon_templates.id'), index=True)
    # 发放时从模板快照，模板后续改动不影响已发出的券
    name: Mapped[str] = mapped_column(String(80))
    amount: Mapped[Decimal] = mapped_column(Numeric(10, 2))
    min_spend: Mapped[Decimal] = mapped_column(Numeric(12, 2), default=0)
    status: Mapped[str] = mapped_column(String(16), default='unused', index=True)  # unused/used/expired
    source: Mapped[str] = mapped_column(String(16), default='verified')  # verified/admin
    issued_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.now())
    expires_at: Mapped[datetime] = mapped_column(DateTime, index=True)
    used_at: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)
    # 与 orders 的关联为普通整型列（非外键），避免 orders/customer_coupons 之间的循环外键
    order_id: Mapped[int | None] = mapped_column(Integer, nullable=True, index=True)
