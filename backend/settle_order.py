"""一次性脚本：补结算指定订单的成功支付（用于回调/查单都失败时的兜底）。

用法：python settle_order.py <order_id>
会查微信侧支付状态，若已支付则按正常流程结算（unpaid -> pending 并发配货邮件）。
"""
import asyncio
import sys

from app.db.session import SessionLocal
from app.models import Order, OrderPayment
from app.services.wechatpay import query_order


async def main(order_id: int):
    from app.api.public import _settle_successful_payment

    db = SessionLocal()
    try:
        payment = (
            db.query(OrderPayment)
            .filter(OrderPayment.order_id == order_id, OrderPayment.status == 'pending')
            .order_by(OrderPayment.id.desc())
            .first()
        )
        if not payment:
            print(f'order {order_id}: 没有 pending 状态的支付流水，无需处理')
            return
        state = query_order(payment.out_trade_no)
        print('微信侧状态:', state.get('pay_status'), 'pay_time:', state.get('pay_time'))
        if state.get('pay_status') != 'ORDER_PAY_SUCC':
            print('微信侧未支付成功，不做结算')
            return
        order = db.query(Order).filter(Order.id == order_id).first()
        print('结算前:', order.status, 'paid:', order.paid_amount)
        await _settle_successful_payment(db, payment, state.get('order_id'))
        db.refresh(order)
        print('结算后:', order.status, 'paid:', order.paid_amount)
    finally:
        db.close()


if __name__ == '__main__':
    asyncio.run(main(int(sys.argv[1])))
