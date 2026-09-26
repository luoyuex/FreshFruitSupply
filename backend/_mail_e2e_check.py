"""临时验证脚本：跑通五类邮件的真实触发路径（不改动业务代码，跑完即删）。"""
import asyncio
from datetime import datetime
from decimal import Decimal

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from app.db.session import Base
import app.models  # noqa: F401
from app.models import Customer, Fruit, Order, OrderItem, OrderNotification, OrderPayment, PriceQuote
from app.core.config import settings
from app.schemas import OrderBulkStatusUpdate, OrderCreate, OrderRefundIn, OrderStatusUpdate
from app.services import email as es

settings.smtp_host = 'smtp.qq.com'
settings.smtp_username = 'sender@qq.com'
settings.smtp_password = 'authcode'
settings.order_notify_email = '853162187@qq.com'
settings.wechat_pay_mock = True

sent = []


async def fake_send(to, subject, body):
    sent.append(subject)


es._send = fake_send

engine = create_engine('sqlite://')
Base.metadata.create_all(engine)
db = sessionmaker(bind=engine)()

fruit = Fruit(id=1, name='麒麟瓜', category='瓜类', spec='8-10斤/个', unit='个', stock_status='in_stock')
fruit.quote = PriceQuote(normal_price=Decimal('45.00'), verified_price=Decimal('42.00'))
db.add(fruit)
db.commit()


def make_order(seq):
    order = Order(
        order_no=f'FF{seq:04d}', customer_id=1, status='unpaid',
        estimated_total=Decimal('45.00'), discount_amount=Decimal('0'), delivery_fee=Decimal('0'),
        payable_total=Decimal('45.00'), paid_amount=Decimal('0'),
        receiver_name='张三', receiver_phone='13800000000',
        province='浙江省', city='杭州市', district='西湖区', detail_address='文一西路 1 号',
    )
    order.items = [OrderItem(fruit_id=1, fruit_name='麒麟瓜', spec='8-10斤/个', unit='个', price=Decimal('45.00'), quantity=Decimal('1'), subtotal=Decimal('45.00'))]
    db.add(order)
    db.commit()
    return order


def pay(order, kind, amount, pending_payload=None):
    payment = OrderPayment(
        order_id=order.id, out_trade_no=f'T{order.id}{kind}', kind=kind, amount=amount,
        status='pending', pending_payload=pending_payload,
    )
    db.add(payment)
    db.commit()
    return payment


async def main():
    from app.api import public as pub
    from app.api import admin as adm

    customer = Customer(id=1, phone='13800000000')
    db.add(customer)
    db.commit()

    # 1) 首付到账 -> dispatch
    o1 = make_order(1)
    await pub._settle_successful_payment(db, pay(o1, 'initial', Decimal('45.00')), 'txn_1')
    db.refresh(o1)
    print('1) 首付后订单状态 =', o1.status, '| 通知 =', [(n.kind, n.status) for n in o1.notifications])

    # 2) 首付只付了一半 -> 仍要发 dispatch，但不推进状态
    o2 = make_order(2)
    await pub._settle_successful_payment(db, pay(o2, 'initial', Decimal('20.00')), 'txn_2')
    db.refresh(o2)
    print('2) 半额首付后订单状态 =', o2.status, '| 通知 =', [(n.kind, n.status) for n in o2.notifications])

    # 3) 订单已关闭后钱才到账 -> stray_payment
    o3 = make_order(3)
    o3.status = 'closed'
    db.commit()
    await pub._settle_successful_payment(db, pay(o3, 'initial', Decimal('45.00')), 'txn_3')
    db.refresh(o3)
    print('3) 关单后到账 ->', [(n.kind, n.status, str(n.refund_amount)) for n in o3.notifications])

    # 4) 改单生效（补差价付满）-> updated
    o4 = make_order(4)
    await pub._settle_successful_payment(db, pay(o4, 'initial', Decimal('45.00')), 'txn_4')
    payload = OrderCreate(
        customer_phone='13800000000', receiver_name='张三', receiver_phone='13800000000',
        province='浙江省', city='杭州市', district='西湖区', detail_address='文一西路 1 号',
        items=[{'fruit_id': 1, 'quantity': Decimal('2')}],
    )
    await pub._settle_successful_payment(
        db, pay(o4, 'supplement', Decimal('45.00'), pending_payload=payload.model_dump_json()), 'txn_5',
    )
    db.refresh(o4)
    print('4) 补差价生效后数量 =', o4.items[0].quantity, '| 通知 =', [(n.kind, n.status, n.attempts) for n in o4.notifications])

    # 5) 不需补款的改单（只改备注）-> updated
    o5 = make_order(5)
    await pub._settle_successful_payment(db, pay(o5, 'initial', Decimal('45.00')), 'txn_6')
    edit = OrderCreate(
        customer_phone='13800000000', receiver_name='张三', receiver_phone='13800000000',
        province='浙江省', city='杭州市', district='西湖区', detail_address='文一西路 1 号',
        delivery_note='改到下午送', items=[{'fruit_id': 1, 'quantity': Decimal('1')}],
    )
    result = await pub.update_order(o5.id, edit, db=db, auth_customer=customer)
    print('5) 仅改备注 need_payment =', result.need_payment, '| 通知 =', [(n.kind, n.status) for n in o5.notifications])

    # 6) 用户自助取消已付款订单 -> refund_customer
    cancelled = await pub.cancel_my_order(o5.id, db=db, auth_customer=customer)
    print('6) 用户取消后状态 =', cancelled.status, '| 通知 =', [(n.kind, n.status, str(n.refund_amount)) for n in cancelled.notifications])

    # 7) 后台退款按钮 -> refund_admin
    o7 = make_order(7)
    await pub._settle_successful_payment(db, pay(o7, 'initial', Decimal('45.00')), 'txn_7')
    await adm.refund_order_payments(o7.id, OrderRefundIn(reason='缺货退这款'), db=db, _=None)
    db.refresh(o7)
    print('7) 后台退款 ->', [(n.kind, n.status, str(n.refund_amount)) for n in o7.notifications])

    # 8) 后台把订单改成已取消（单个 + 批量）-> refund_admin
    o8 = make_order(8)
    await pub._settle_successful_payment(db, pay(o8, 'initial', Decimal('45.00')), 'txn_8')
    await adm.update_order_status(o8.id, OrderStatusUpdate(status='cancelled'), db=db, _=None)
    db.refresh(o8)
    print('8a) 后台单个取消 ->', [(n.kind, n.status) for n in o8.notifications])

    o9 = make_order(9)
    await pub._settle_successful_payment(db, pay(o9, 'initial', Decimal('45.00')), 'txn_9')
    await adm.bulk_update_order_status(OrderBulkStatusUpdate(order_ids=[o9.id], status='cancelled'), db=db, _=None)
    db.refresh(o9)
    print('8b) 后台批量取消 ->', [(n.kind, n.status) for n in o9.notifications])

    # 9) 未付款订单在后台取消：不退钱，也不该发退款邮件
    o10 = make_order(10)
    await adm.update_order_status(o10.id, OrderStatusUpdate(status='cancelled'), db=db, _=None)
    db.refresh(o10)
    print('9) 未付款后台取消 -> 状态', o10.status, '| 通知 =', [(n.kind, n.status) for n in o10.notifications])

    # 10) 重发接口 + 序列化
    rec = await adm.resend_order_notice(o1.id, 'dispatch', db=db, _=None)
    print('10) 重发返回', [(item.kind, item.status, item.attempts) for item in rec])
    from app.schemas import OrderOut
    out = OrderOut.model_validate(db.query(Order).filter(Order.id == o1.id).first())
    print('    OrderOut.notifications =', [n.model_dump() for n in out.notifications][:1])

    print('\n实际发出的邮件主题：')
    for subject in sent:
        print(' -', subject)
    print('\n投递记录合计：', [(n.kind, n.status) for n in db.query(OrderNotification).order_by(OrderNotification.order_id, OrderNotification.kind).all()])


asyncio.run(main())
