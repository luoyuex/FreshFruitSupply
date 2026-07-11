from email.message import EmailMessage

import aiosmtplib

from app.core.config import settings
from app.models import Order


def _build_order_body(order: Order) -> str:
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
    lines.extend(['', f'预估总价：{order.estimated_total}'])
    if order.discount_amount and order.discount_amount > 0:
        lines.append(f'优惠券抵扣：-{order.discount_amount}')
        lines.append(f'实付：{order.payable_total}')
    return '\n'.join(lines)


async def send_order_email(order: Order) -> None:
    if not all([settings.smtp_host, settings.smtp_username, settings.smtp_password, settings.order_notify_email]):
        raise RuntimeError('SMTP settings are incomplete')

    message = EmailMessage()
    message['From'] = settings.smtp_from or settings.smtp_username
    message['To'] = settings.order_notify_email
    message['Subject'] = f'新的水果预订订单：{order.order_no}'
    message.set_content(_build_order_body(order))

    await aiosmtplib.send(
        message,
        hostname=settings.smtp_host,
        port=settings.smtp_port,
        username=settings.smtp_username,
        password=settings.smtp_password,
        use_tls=settings.smtp_port == 465,
        start_tls=settings.smtp_port != 465,
    )
