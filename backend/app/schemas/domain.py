from datetime import datetime
from decimal import Decimal
from typing import List, Literal

from pydantic import BaseModel, ConfigDict, Field, field_serializer

from app.services.upload import to_public_url, to_public_urls


class QuoteOut(BaseModel):
    normal_price: Decimal
    verified_price: Decimal
    grade: str
    min_order_quantity: Decimal
    note: str | None = None
    updated_at: datetime | None = None

    model_config = ConfigDict(from_attributes=True)


class FruitCategoryOut(BaseModel):
    id: int
    name: str
    icon: str | None = None
    icon_url: str | None = None
    sort_order: int
    is_active: bool

    model_config = ConfigDict(from_attributes=True)

    @field_serializer('icon_url')
    def serialize_icon_url(self, value: str | None):
        return to_public_url(value)


class FruitCategoryUpsert(BaseModel):
    name: str
    icon: str | None = None
    icon_url: str | None = None
    sort_order: int = 0
    is_active: bool = True


class FruitOut(BaseModel):
    id: int
    category_id: int | None = None
    name: str
    category: str
    image_url: str | None = None
    image_urls: List[str] = Field(default_factory=list)
    detail_image_urls: List[str] = Field(default_factory=list)
    origin: str | None = None
    spec: str
    unit: str
    stock_status: str
    is_recommended: bool
    quote: QuoteOut | None = None

    model_config = ConfigDict(from_attributes=True)

    @field_serializer('image_url')
    def serialize_image_url(self, value: str | None):
        return to_public_url(value)

    @field_serializer('image_urls', 'detail_image_urls')
    def serialize_image_urls(self, value: List[str]):
        return to_public_urls(value)


class FruitUpsert(BaseModel):
    name: str
    category_id: int
    category: str | None = None
    image_url: str | None = None
    image_urls: List[str] = Field(default_factory=list)
    detail_image_urls: List[str] = Field(default_factory=list)
    origin: str | None = None
    spec: str
    unit: str = '斤'
    stock_status: str = 'in_stock'
    is_recommended: bool = False
    normal_price: Decimal = Field(gt=0)
    verified_price: Decimal = Field(gt=0)
    grade: str = '一级'
    min_order_quantity: Decimal = Field(default=1, gt=0)
    note: str | None = None


class CustomerOut(BaseModel):
    id: int
    phone: str
    wechat_openid: str | None = None
    nickname: str | None = None
    avatar_url: str | None = None
    verification_status: str
    shop_name: str | None = None
    contact_name: str | None = None
    business_type: str | None = None

    model_config = ConfigDict(from_attributes=True)

    @field_serializer('avatar_url')
    def serialize_avatar_url(self, value: str | None):
        return to_public_url(value)


class CustomerAddressOut(BaseModel):
    id: int
    receiver_name: str
    receiver_phone: str
    province: str
    city: str
    district: str
    detail_address: str
    delivery_note: str | None = None
    is_default: bool
    latitude: float | None = None
    longitude: float | None = None

    model_config = ConfigDict(from_attributes=True)


class CustomerAddressUpsert(BaseModel):
    receiver_name: str
    receiver_phone: str
    province: str
    city: str
    district: str
    detail_address: str
    delivery_note: str | None = None
    is_default: bool = False
    latitude: float | None = None
    longitude: float | None = None


class VerificationOut(BaseModel):
    id: int
    customer_id: int
    shop_name: str
    contact_name: str
    phone: str
    business_type: str
    image_urls: List[str]
    status: str
    review_note: str | None = None
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)


class VerificationReview(BaseModel):
    status: str = Field(pattern='^(verified|rejected)$')
    review_note: str | None = None


class OrderItemCreate(BaseModel):
    fruit_id: int
    quantity: Decimal = Field(gt=0)


class OrderCreate(BaseModel):
    customer_phone: str
    wechat_openid: str | None = None
    receiver_name: str
    receiver_phone: str
    province: str
    city: str
    district: str
    detail_address: str
    delivery_note: str | None = None
    items: List[OrderItemCreate]
    coupon_id: int | None = None


class OrderItemOut(BaseModel):
    id: int
    fruit_id: int
    fruit_name: str
    image_url: str | None = None
    spec: str
    unit: str
    price: Decimal
    quantity: Decimal
    subtotal: Decimal

    model_config = ConfigDict(from_attributes=True)

    @field_serializer('image_url')
    def serialize_image_url(self, value: str | None):
        return to_public_url(value)


class OrderOut(BaseModel):
    id: int
    order_no: str
    customer_id: int
    status: str
    estimated_total: Decimal
    discount_amount: Decimal = Decimal('0')
    delivery_fee: Decimal = Decimal('0')
    payable_total: Decimal = Decimal('0')
    coupon_id: int | None = None
    receiver_name: str
    receiver_phone: str
    province: str
    city: str
    district: str
    detail_address: str
    delivery_note: str | None = None
    email_notify_status: str
    can_edit: bool = False
    created_at: datetime
    items: List[OrderItemOut]

    model_config = ConfigDict(from_attributes=True)


class OrderStatusUpdate(BaseModel):
    status: str = Field(pattern='^(pending|confirmed|delivering|completed|cancelled)$')


class OrderBulkStatusUpdate(OrderStatusUpdate):
    order_ids: List[int] = Field(min_length=1)


class CouponTemplateOut(BaseModel):
    id: int
    name: str
    description: str | None = None
    discount_type: str
    amount: Decimal
    min_spend: Decimal
    valid_days: int
    grant_on_verified: bool
    per_customer_limit: int
    is_active: bool

    model_config = ConfigDict(from_attributes=True)


class CouponTemplateUpsert(BaseModel):
    name: str
    description: str | None = None
    amount: Decimal = Field(ge=0)
    min_spend: Decimal = Field(default=0, ge=0)
    valid_days: int = Field(default=30, gt=0)
    grant_on_verified: bool = False
    per_customer_limit: int = Field(default=1, ge=1)
    is_active: bool = True


class CouponGrantIn(BaseModel):
    template_id: int


class CustomerCouponOut(BaseModel):
    id: int
    name: str
    amount: Decimal
    min_spend: Decimal
    status: str
    source: str
    issued_at: datetime | None = None
    expires_at: datetime
    used_at: datetime | None = None
    order_id: int | None = None

    model_config = ConfigDict(from_attributes=True)


class DeliveryConfigOut(BaseModel):
    # 包邮门槛与配送费，前端下单页据此估算、后台设置页据此回填
    free_threshold: Decimal
    fee: Decimal


class DeliveryConfigUpdate(BaseModel):
    free_threshold: Decimal = Field(ge=0)
    fee: Decimal = Field(ge=0)


class SalesStatsItemOut(BaseModel):
    fruit_id: int
    fruit_name: str
    spec: str
    unit: str
    quantity: Decimal
    subtotal: Decimal
    order_count: int


class SalesStatsStatusOut(BaseModel):
    status: str
    order_count: int
    amount: Decimal


class SalesStatsOut(BaseModel):
    date: str
    order_count: int
    item_kind_count: int
    total_quantity: Decimal
    estimated_total: Decimal
    items: List[SalesStatsItemOut]
    statuses: List[SalesStatsStatusOut]


class AdminLogin(BaseModel):
    username: str
    password: str


class AdminOut(BaseModel):
    id: int
    username: str
    role: str
    wechat_openid: str | None = None
    nickname: str | None = None
    is_active: bool
    created_at: datetime | None = None

    model_config = ConfigDict(from_attributes=True)


class AdminUpsert(BaseModel):
    username: str
    role: Literal['super_admin', 'order_admin'] = 'order_admin'
    wechat_openid: str | None = None
    nickname: str | None = None
    is_active: bool = True
    password: str | None = None


class AdminPasswordUpdate(BaseModel):
    password: str = Field(min_length=6)


class TokenOut(BaseModel):
    access_token: str
    token_type: str = 'bearer'


class AdminAuthOut(TokenOut):
    admin: AdminOut
    permissions: List[str]


class AdminEntryVisibleOut(BaseModel):
    visible: bool


class CustomerAdminOut(CustomerOut):
    created_at: datetime | None = None
    order_count: int = 0
    latest_order_at: datetime | None = None


class WechatLoginIn(BaseModel):
    code: str


class CustomerAuthOut(BaseModel):
    access_token: str
    token_type: str = 'bearer'
    customer: CustomerOut
    is_phone_bound: bool


class CustomerProfileUpdate(BaseModel):
    nickname: str | None = None
    avatar_url: str | None = None
    contact_name: str | None = None
    phone: str | None = None
