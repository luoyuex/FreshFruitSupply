"""待支付订单超时自动关闭。

下单生成 unpaid 订单后若超过 order_unpaid_timeout_minutes 分钟仍未支付，
自动置为 closed 并释放其占用的优惠券（无需退款——从未支付成功）。

关闭前会同步关闭微信侧预支付单，否则用户超时后仍能在微信里完成付款，
导致「订单已关闭但钱已收」；万一关单失败且查单显示已支付，则放弃本次关单，
交由支付回调或主动查单接口结算。

由应用启动时拉起的 asyncio 定时任务周期调用 close_expired_unpaid_orders；
也可单独调用（如测试）。所有 DB 会话在函数内自建自关，独立于请求生命周期。
"""
from __future__ import annotations

import asyncio
from datetime import datetime, timedelta
from decimal import Decimal

from fastapi import HTTPException

from app.core.config import settings
from app.db.session import SessionLocal
from app.models import Order, OrderPayment
from app.services import wechatpay
from app.services.coupon import release_order_coupons
from sqlalchemy.orm import Session

# 扫描周期：每 60 秒检查一次到期的待支付订单
SCAN_INTERVAL_SECONDS = 60

# 已付款订单取消后进入的目标状态（已退款）
CANCELLED_STATUS = 'cancelled'
# 未付款订单取消/超时后进入的目标状态（无需退款）
CLOSED_STATUS = 'closed'


def refund_order(db: Session, order: Order) -> None:
    """退掉订单下所有已成功的支付流水，原路退款。

    对每笔 success 流水调用微信退款，成功后标记为 refunded 并回写 refund_id；
    退款金额从 order.paid_amount 扣减。调用方负责设置订单最终状态与提交事务。
    Mock 模式下退款直接视为成功。
    """
    success_payments = (
        db.query(OrderPayment)
        .filter(OrderPayment.order_id == order.id, OrderPayment.status == 'success')
        .all()
    )
    for payment in success_payments:
        result = wechatpay.refund(payment)
        payment.status = 'refunded'
        payment.refund_id = result.get('refund_id')
        payment.refunded_at = datetime.now()
        order.paid_amount = (order.paid_amount or Decimal('0')) - payment.amount
    if order.paid_amount < 0:
        order.paid_amount = Decimal('0')


def _close_pending_payments(db: Session, order: Order) -> bool:
    """关闭订单下所有待支付流水：先关微信侧预支付单，再本地作废。

    返回 False 表示关单失败且查单确认已支付——此时不能关单，应由回调/主动查单结算。
    """
    pending_payments = (
        db.query(OrderPayment)
        .filter(OrderPayment.order_id == order.id, OrderPayment.status == 'pending')
        .all()
    )
    for payment in pending_payments:
        try:
            if not wechatpay.close_order(payment.out_trade_no) and _is_paid_at_wechat(payment.out_trade_no):
                return False
        except Exception:
            # 微信不可用/未配置：按未支付继续本地关单；万一钱真到账，结算逻辑会原路退回
            pass
        payment.status = 'cancelled'
    return True


def _is_paid_at_wechat(out_trade_no: str) -> bool:
    """关单失败时查单确认是否已支付——已支付则不能再关单，应由回调/主动查单结算。"""
    try:
        return wechatpay.query_order(out_trade_no).get('trade_state') == 'SUCCESS'
    except Exception:
        return False


def cancel_order(db: Session, order: Order) -> Decimal:
    """取消订单：已付款则原路退款并置 cancelled，未付款直接 closed。两者都释放占用的券。

    返回实际退回的金额（未付款订单为 0），供调用方决定是否通知商户。
    供用户端与后台取消共用。调用方负责鉴权与提交事务。
    """
    refunded_amount = order.paid_amount or Decimal('0')
    if refunded_amount > 0:
        refund_order(db, order)
        order.status = CANCELLED_STATUS
    else:
        if not _close_pending_payments(db, order):
            # 微信侧查单确认已支付：不能按未支付关单，否则会出现「本地已关、钱还没退」的脱节窗口。
            # 交给支付回调/主动查单结算（会自动原路退回），调用方收到报错后让用户稍后再试。
            raise HTTPException(status_code=409, detail='订单支付状态确认中，请稍后再试或联系客服')
        refunded_amount = Decimal('0')
        order.status = CLOSED_STATUS
    release_order_coupons(db, order)
    return refunded_amount


def close_expired_unpaid_orders() -> int:
    """关闭所有超时未支付的订单，返回本次关闭数量。

    以 created_at 判断是否超过配置的超时时长；关闭时先关微信侧预支付单，
    再置 closed 并释放占用的券。若查单显示已支付则跳过，留给回调结算。
    """
    timeout_minutes = settings.order_unpaid_timeout_minutes
    if timeout_minutes <= 0:
        return 0
    deadline = datetime.now() - timedelta(minutes=timeout_minutes)
    db = SessionLocal()
    try:
        expired = (
            db.query(Order)
            .filter(Order.status == 'unpaid', Order.created_at < deadline)
            .all()
        )
        closed = 0
        for order in expired:
            if not _close_pending_payments(db, order):
                continue
            order.status = 'closed'
            release_order_coupons(db, order)
            closed += 1
        if expired:
            db.commit()
        return closed
    finally:
        db.close()


async def _run_periodic_close() -> None:
    while True:
        await asyncio.sleep(SCAN_INTERVAL_SECONDS)
        try:
            # 关单是同步 DB 操作，丢到线程池避免阻塞事件循环
            await asyncio.to_thread(close_expired_unpaid_orders)
        except Exception:
            # 单次扫描异常不应终止循环，等待下一周期重试
            pass


def start_unpaid_order_closer() -> asyncio.Task:
    """启动后台超时关单任务，返回可用于取消的 Task。"""
    return asyncio.create_task(_run_periodic_close())
