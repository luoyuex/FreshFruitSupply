"""订单场景邮件的统一出口：配好正文所需的补送券再发信，投递结果落 order_notifications。

邮件分五类（新单配货 / 改单 / 客户取消退款 / 后台退款 / 关单后到账退回），
判定见 app.services.email。发信失败不抛出、只记 failed，由管理后台重发。
"""
from decimal import Decimal

from sqlalchemy.orm import Session

from app.models import Order
from app.services.coupon import attach_reissue_coupons
from app.services.email import notify_order


async def notify_merchant(
    db: Session,
    order: Order,
    kind: str,
    refunded_amount: Decimal | None = None,
) -> None:
    """给商户发一封该订单的场景邮件。

    先挂补送券，正文才带得上补送商品明细；notify_order 会提交事务、使订单上的
    临时属性失效，故发完再挂一次，供接口响应序列化。
    """
    attach_reissue_coupons(db, [order])
    await notify_order(db, order, kind, refunded_amount)
    attach_reissue_coupons(db, [order])
