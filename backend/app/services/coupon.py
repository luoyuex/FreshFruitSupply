from datetime import datetime, timedelta
from decimal import Decimal

from sqlalchemy.orm import Session

from app.models import CouponTemplate, Customer, CustomerCoupon


def grant_coupons_on_verified(db: Session, customer: Customer) -> list[CustomerCoupon]:
    """认证通过时，发放所有配置为 grant_on_verified 的券。

    幂等：按模板的 per_customer_limit 限制每人持有数量（统计历史累计发放数，
    因此认证再次通过也不会重复发放）。调用方负责随后 commit。
    """
    granted: list[CustomerCoupon] = []
    templates = (
        db.query(CouponTemplate)
        .filter(CouponTemplate.grant_on_verified.is_(True), CouponTemplate.is_active.is_(True))
        .all()
    )
    now = datetime.now()
    for template in templates:
        held = (
            db.query(CustomerCoupon)
            .filter(
                CustomerCoupon.customer_id == customer.id,
                CustomerCoupon.template_id == template.id,
            )
            .count()
        )
        if held >= template.per_customer_limit:
            continue
        coupon = CustomerCoupon(
            customer_id=customer.id,
            template_id=template.id,
            name=template.name,
            amount=template.amount,
            min_spend=template.min_spend,
            status='unused',
            source='verified',
            issued_at=now,
            expires_at=now + timedelta(days=template.valid_days),
        )
        db.add(coupon)
        granted.append(coupon)
    return granted


def compute_discount(coupon: CustomerCoupon, goods_total: Decimal) -> Decimal:
    """给定券与商品原价合计，返回抵扣额。

    未达满减门槛返回 0；抵扣额不超过商品合计（避免出现负数实付）。
    该口径与前端 utils/coupon.js 的 couponDiscount 保持一致。
    """
    goods_total = Decimal(goods_total)
    if goods_total < Decimal(coupon.min_spend or 0):
        return Decimal('0')
    return min(Decimal(coupon.amount), goods_total)
