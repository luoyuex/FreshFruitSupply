from datetime import datetime
from decimal import Decimal
from email.message import EmailMessage

import aiosmtplib
from sqlalchemy.orm import Session

from app.core.config import settings
from app.models import Order, OrderNotification

# 场景邮件类型：一类一封，同一订单每类只保留一条投递记录（重发覆盖状态、累加次数）
KIND_DISPATCH = 'dispatch'  # 新单付满，通知配货
KIND_UPDATED = 'updated'  # 改单生效，按最新明细配货
KIND_REFUND_CUSTOMER = 'refund_customer'  # 客户自助取消并退款
KIND_REFUND_ADMIN = 'refund_admin'  # 商户在后台发起退款/取消
KIND_STRAY_PAYMENT = 'stray_payment'  # 订单已关闭后才到账，已原路退回
NOTIFY_KINDS = (KIND_DISPATCH, KIND_UPDATED, KIND_REFUND_CUSTOMER, KIND_REFUND_ADMIN, KIND_STRAY_PAYMENT)

_KIND_SUBJECTS = {
    KIND_DISPATCH: '新的水果预订订单',
    KIND_UPDATED: '订单已修改',
    KIND_REFUND_CUSTOMER: '客户取消并退款',
    KIND_REFUND_ADMIN: '商户后台退款',
    KIND_STRAY_PAYMENT: '订单关闭后到账已退回',
}


def _ensure_smtp_configured() -> None:
    if not all([settings.smtp_host, settings.smtp_username, settings.smtp_password, settings.order_notify_email]):
        raise RuntimeError('SMTP settings are incomplete')


def _order_detail_lines(order: Order) -> list[str]:
    """订单公共明细（收货信息 + 商品 + 金额），五类通知共用。"""
    lines = [
        f'订单号：{order.order_no}',
        f'订单状态：{order.status}',
        f'客户ID：{order.customer_id}',
        f'收货人：{order.receiver_name}',
        f'手机号：{order.receiver_phone}',
        f'地址：{order.province}{order.city}{order.district}{order.detail_address}',
        f'配送备注：{order.delivery_note or "无"}',
        '',
        '商品明细：',
    ]
    for item in order.items:
        lines.append(f'- {item.fruit_name} {item.spec} x {item.quantity}{item.unit}，单价 {item.price}，小计 {item.subtotal}')
    # 商品补送券（配货时随单免费补配，无金额）。属性由 attach_reissue_coupons 挂载，未挂载时视为空
    reissue_coupons = getattr(order, 'reissue_coupons', None) or []
    if reissue_coupons:
        lines.extend(['', '补送商品（随单免费补配）：'])
        for coupon in reissue_coupons:
            note = f'（{coupon.description}）' if coupon.description else ''
            lines.append(f'- {coupon.name}{note}')
    lines.extend(['', f'预估总价：{order.estimated_total}'])
    if order.discount_amount and order.discount_amount > 0:
        lines.append(f'优惠券抵扣：-{order.discount_amount}')
    if order.delivery_fee and order.delivery_fee > 0:
        lines.append(f'配送费：+{order.delivery_fee}')
    else:
        lines.append('配送费：免（已满包邮门槛）')
    lines.append(f'实付：{order.payable_total}')
    return lines


def _refund_lines(kind: str, refunded_amount: Decimal | None) -> list[str]:
    """退款类邮件开头：告诉商户该不该停手，以及退了多少钱。"""
    amount_text = f'{refunded_amount} 元' if refunded_amount is not None else '见后台流水'
    if kind == KIND_REFUND_CUSTOMER:
        return ['客户已取消该订单，商户尚未确认，无需配货。', f'已支付款项原路退回：{amount_text}。']
    if kind == KIND_REFUND_ADMIN:
        return ['商户已在后台对该订单发起退款，请暂停配货并核实备货进度。', f'本次退款金额：{amount_text}。']
    return ['款项到账时订单已关闭或已取消，已原路退回，无需配货。', f'退回金额：{amount_text}。']


def _build_body(order: Order, kind: str, refunded_amount: Decimal | None) -> str:
    if kind == KIND_DISPATCH:
        head = ['客户已完成支付，请安排配货。']
    elif kind == KIND_UPDATED:
        head = ['客户修改了该订单，以下为最新明细，请按新明细配货。']
    else:
        head = _refund_lines(kind, refunded_amount)
    return '\n'.join([*head, '', *_order_detail_lines(order)])


async def _send(to: str, subject: str, body: str) -> None:
    message = EmailMessage()
    message['From'] = settings.smtp_from or settings.smtp_username
    message['To'] = to
    message['Subject'] = subject
    message.set_content(body)

    await aiosmtplib.send(
        message,
        hostname=settings.smtp_host,
        port=settings.smtp_port,
        username=settings.smtp_username,
        password=settings.smtp_password,
        use_tls=settings.smtp_port == 465,
        start_tls=settings.smtp_port != 465,
    )


def _notification_record(db: Session, order: Order, kind: str, refunded_amount: Decimal | None) -> OrderNotification:
    """取该订单该场景的投递记录，没有则新建；退款金额以最近一次触发时的数额为准，供重发还原文案。"""
    record = (
        db.query(OrderNotification)
        .filter(OrderNotification.order_id == order.id, OrderNotification.kind == kind)
        .first()
    )
    if not record:
        record = OrderNotification(order_id=order.id, kind=kind, status='pending')
        db.add(record)
    if refunded_amount is not None:
        record.refund_amount = refunded_amount
    return record


async def notify_order(
    db: Session,
    order: Order,
    kind: str,
    refunded_amount: Decimal | None = None,
) -> OrderNotification:
    """按场景给商户发通知邮件，并把投递结果落到 order_notifications。

    发信失败只在记录上标 failed、不向上抛：邮件是提醒手段，不能因为网络抖动或 SMTP
    配置缺失回滚订单状态。调用方需先 attach_reissue_coupons，正文才会带上补送商品明细。
    """
    record = _notification_record(db, order, kind, refunded_amount)
    subject = f'{_KIND_SUBJECTS[kind]}：{order.order_no}'
    error: str | None = None
    try:
        _ensure_smtp_configured()
        await _send(settings.order_notify_email, subject, _build_body(order, kind, record.refund_amount))
    except Exception as exc:  # noqa: BLE001 - 任何发信异常都只标记失败，交给后台重发
        error = str(exc) or exc.__class__.__name__

    record.attempts += 1
    record.status = 'failed' if error else 'sent'
    record.error = error
    record.sent_at = None if error else datetime.now()
    order.email_notify_status = record.status
    db.commit()
    return record
