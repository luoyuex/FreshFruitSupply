"""临时诊断：查询指定流水在微信侧的支付状态（只读，不做任何写操作）。"""
from app.db.session import SessionLocal
from app.models import Order
from app.services.wechatpay import query_order

TRADE_NOS = [
    'P178998038533149d80a73',  # payment id=34 / order 34
]

db = SessionLocal()
try:
    for no in TRADE_NOS:
        try:
            state = query_order(no)
            print(no, '->', state.get('pay_status'), 'pay_time:', state.get('pay_time'), 'order_id:', state.get('order_id'), state.get('amount'))
        except Exception as exc:
            print(no, '-> 查询失败:', exc)
    for order in db.query(Order).filter(Order.id.in_([31, 32])).all():
        print(f'order {order.id}: status={order.status} paid={order.paid_amount} payable={order.payable_total}')
finally:
    db.close()
