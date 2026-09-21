"""一次性脚本：对账指定订单的支付流水并驱动结算/自动退款。

用法：python settle_order.py <order_id>
查微信侧支付状态，若已支付则走 _settle_successful_payment：
- 订单有效（unpaid）→ 正常结算为待确认并配货；
- 订单已关闭/取消、或流水已被误作废 → 自动原路退款（钱退回用户）。
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
            .filter(OrderPayment.order_id == order_id)
            .order_by(OrderPayment.id.desc())
            .first()
        )
        if not payment:
            print(f'order {order_id}: 没有支付流水，无需处理')
            return
        if payment.status in ('refunded', 'refund_failed'):
            print(f'payment {payment.out_trade_no} 状态已是 {payment.status}，无需处理')
            return
        state = query_order(payment.out_trade_no)
        print('微信侧状态:', state.get('pay_status'), 'pay_time:', state.get('pay_time'))
        if state.get('pay_status') != 'ORDER_PAY_SUCC':
            print('微信侧未支付成功，不做结算')
            return
        order = db.query(Order).filter(Order.id == order_id).first()
        print('结算前:', order.status, 'paid:', order.paid_amount, 'payment:', payment.status)
        await _settle_successful_payment(db, payment, state.get('order_id'))
        db.refresh(order)
        db.refresh(payment)
        print('结算后:', order.status, 'paid:', order.paid_amount, 'payment:', payment.status)
    finally:
        db.close()


if __name__ == '__main__':
    asyncio.run(main(int(sys.argv[1])))
