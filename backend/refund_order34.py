"""一次性脚本：直接向微信发起订单 34 的原路退款（不依赖本地数据库）。"""
from decimal import Decimal

from app.services.wechatpay import query_order, refund

TRADE_NO = 'P178998038533149d80a73'  # 订单 34，实付 21 元


class _Payment:
    out_trade_no = TRADE_NO
    amount = Decimal('21.00')


state = query_order(TRADE_NO)
print('微信侧状态:', state.get('pay_status'))
if state.get('pay_status') != 'ORDER_PAY_SUCC':
    print('微信侧未支付成功，不退款')
else:
    result = refund(_Payment())
    print('退款已受理, refund_id:', result.get('refund_id'))
    after = query_order(TRADE_NO)
    print('退款后状态:', after.get('pay_status'))
