"""一次性修复脚本：结算误付订单 → 原路退款；关闭未支付的预下单。"""
import asyncio

from app.db.session import SessionLocal
from app.models import Order, OrderPayment
from app.services.order_maintenance import cancel_order
from app.services.wechatpay import _b2b_post, _dumps, _server_appkey, _pay_sig, query_order
from app.core.config import settings

PAID_TRADE_NO = 'P178997748521147163b2a'   # ORDER_PAY_SUCC，实付 21 元
UNPAID_TRADE_NO = 'P1789977465231867278dc'  # ORDER_PRE_PAY，未支付


def close_b2b_prepay(out_trade_no: str) -> None:
    """直接关微信侧预下单（绕过 query_order 判断，因为已知它处于 PRE_PAY）。"""
    import urllib.error
    import urllib.parse
    import urllib.request
    from app.services.wechat import get_access_token

    url_path = '/retail/B2b/closeb2border'
    body = _dumps({'mchid': settings.wechat_pay_mchid, 'out_trade_no': out_trade_no})
    query = urllib.parse.urlencode({
        'access_token': get_access_token(),
        'pay_sig': _pay_sig(url_path, body, _server_appkey()),
    })
    request = urllib.request.Request(
        'https://api.weixin.qq.com' + url_path + '?' + query,
        data=body.encode('utf-8'),
        headers={'Content-Type': 'application/json'},
        method='POST',
    )
    with urllib.request.urlopen(request, timeout=15) as response:
        print('close', out_trade_no, '->', response.read().decode('utf-8'))


async def main():
    from app.api.public import _settle_successful_payment

    db = SessionLocal()
    try:
        # 1) 结算订单 32：让后端按正常流程把这笔成功支付落账（unpaid -> pending）
        payment = db.query(OrderPayment).filter(OrderPayment.out_trade_no == PAID_TRADE_NO).first()
        order = db.query(Order).filter(Order.id == payment.order_id).first()
        print('order', order.id, 'before:', order.status, 'paid:', order.paid_amount)
        await _settle_successful_payment(db, payment, 'o202609211558053320424759')
        db.refresh(order)
        print('order', order.id, 'settled:', order.status, 'paid:', order.paid_amount)

        # 2) 取消订单 32：走系统自带退款（原路退回 21 元）
        refunded = cancel_order(db, order)
        db.commit()
        db.refresh(order)
        print('order', order.id, 'cancelled, refund initiated:', refunded, 'payment status:',
              db.query(OrderPayment).filter(OrderPayment.out_trade_no == PAID_TRADE_NO).first().status)

        # 3) 关闭订单 31 的预下单（未支付，无退款）
        p31 = db.query(OrderPayment).filter(OrderPayment.out_trade_no == UNPAID_TRADE_NO).first()
        close_b2b_prepay(UNPAID_TRADE_NO)
        p31.status = 'cancelled'
        o31 = db.query(Order).filter(Order.id == p31.order_id).first()
        o31.status = 'closed'
        db.commit()
        print('order 31 closed, payment cancelled')

        # 4) 终态确认
        state = query_order(PAID_TRADE_NO)
        print('final wechat state of paid trade:', state.get('pay_status'))
    finally:
        db.close()


asyncio.run(main())
