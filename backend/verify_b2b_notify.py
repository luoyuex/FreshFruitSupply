"""临时验证：支付通知验签与「以查单为准」的结算门槛。跑完即删。"""
import asyncio
from decimal import Decimal

from fastapi import HTTPException

from app.api import public
from app.core.config import settings

settings.wechat_b2b_msg_token = 'unit-test-token'
settings.wechat_pay_mock = False

results = []


def check(name, got, want):
    ok = got == want
    results.append((ok, name, got, want))
    print(('  PASS  ' if ok else '  FAIL  ') + name + (f'  got={got!r} want={want!r}' if not ok else ''))


class FakePayment:
    out_trade_no = 'P_UNIT_1'
    amount = Decimal('21.00')


# ---------- 1. 纯函数 ----------
print('\n[1] _query_amount_fen / _txn_id')
check('裸整型 amount 量纲不可信 → 跳过核对', public._query_amount_fen({'amount': 2100}), None)
check('裸数字串 amount → 跳过核对', public._query_amount_fen({'amount': '2100'}), None)
check('dict + 白名单键 payer_total', public._query_amount_fen({'amount': {'payer_total': 2100}}), 2100)
check('dict 键顺序无关(靠白名单)', public._query_amount_fen({'amount': {'currency': 'CNY', 'order_amount': 500}}), 500)
check('不被 refund_amount=0 抢先', public._query_amount_fen({'amount': {'refund_amount': 0, 'total': 2100}}), 2100)
check('非白名单键不猜', public._query_amount_fen({'amount': {'foo': 2100}}), None)
check('amount 是元(小数)时不猜', public._query_amount_fen({'amount': 21.00}), None)
check('amount 缺失', public._query_amount_fen({}), None)
check('bool 不当金额取', public._query_amount_fen({'amount': {'total': True}}), None)
check('字符串分可信', public._query_amount_fen({'amount': {'total_fee': '2100'}}), 2100)
check('查单流水号取 order_id', public._txn_id({'order_id': 'TX9'}), 'TX9')
check('兼容通知字段名', public._txn_id({'wxpay_transaction_id': 'TX8'}), 'TX8')

# ---------- 2. 验签 ----------
print('\n[2] _b2b_msg_signature_ok')
import hashlib
ts, nonce = '1700000000', 'abc123'
good = hashlib.sha1(''.join(sorted([ts, nonce, 'unit-test-token'])).encode()).hexdigest()
check('正确签名通过', public._b2b_msg_signature_ok(good, ts, nonce), True)
check('错误签名拒绝', public._b2b_msg_signature_ok('deadbeef', ts, nonce), False)
check('缺签名拒绝', public._b2b_msg_signature_ok(None, ts, nonce), False)
check('Token 未配置一律拒绝', public._b2b_msg_signature_ok(good, ts, nonce) if settings.wechat_b2b_msg_token else None, True)
settings.wechat_b2b_msg_token = ''
check('Token 置空后拒绝(fail-closed)', public._b2b_msg_signature_ok(good, ts, nonce), False)
settings.wechat_b2b_msg_token = 'unit-test-token'

# ---------- 3. 结算前查单确认 ----------
print('\n[3] _confirm_paid_at_wechat 以查单为准')
query_backup = public.query_order
mock_backup = public.is_mock


def run_confirm(state=None, raises=None):
    def fake_query(_no):
        if raises:
            raise raises
        return state
    public.query_order = fake_query
    public.is_mock = lambda: False
    try:
        return asyncio.run(public._confirm_paid_at_wechat(FakePayment(), {'pay_status': 'ORDER_PAY_SUCC'}))
    finally:
        public.query_order = query_backup
        public.is_mock = mock_backup


outcome, txn = run_confirm({'pay_status': 'ORDER_PAY_SUCC', 'order_id': 'TX1', 'amount': {'payer_total': 2100}})
check('查单确认+金额吻合(分) → 结算', (outcome, txn), ('confirmed', 'TX1'))
check('未确认 → 不结算', run_confirm({'pay_status': 'ORDER_PRE_PAY'})[0], 'unconfirmed')
check('查单报错 → 不结算', run_confirm(raises=HTTPException(502, detail='x'))[0], 'unconfirmed')
check('金额不符 → 拒绝结算', run_confirm({'pay_status': 'ORDER_PAY_SUCC', 'order_id': 'TX2', 'amount': {'payer_total': 1}})[0], 'mismatch')
check('金额无法解析 → 放行但告警', run_confirm({'pay_status': 'ORDER_PAY_SUCC', 'order_id': 'TX3'})[0], 'confirmed')
check('裸数字量纲不明 → 放行不误拒', run_confirm({'pay_status': 'ORDER_PAY_SUCC', 'order_id': 'TX4', 'amount': 21})[0], 'confirmed')
check('通知称已付但查单未付 → 不结算(伪造失效)', run_confirm({'pay_status': 'ORDER_PRE_PAY', 'amount': {'payer_total': 1}})[0], 'unconfirmed')

# ---------- 4. 接口层：无签名进不来 ----------
print('\n[4] HTTP 接口验签闸门')
class FakeRequest:
    """只带 handler 真正用到的三样：method / query_params / json()。"""

    def __init__(self, method='POST', query=None, body=None):
        self.method = method
        self.query_params = query or {}
        self._body = body

    async def json(self):
        if isinstance(self._body, Exception):
            raise self._body
        return self._body


class FakeDb:
    def __init__(self, payment='absent'):
        self.payment = None if payment == 'absent' else (payment or FakePayment())

    def query(self, *a, **kw):
        outer = self

        class Q:
            def filter(self, *a, **kw):
                return self

            def first(self):
                return outer.payment
        return Q()


def call(method='POST', query=None, body=None, db=None):
    return asyncio.run(public.b2b_pay_notify(FakeRequest(method, query, body), db=db or FakeDb()))


def signed(query_extra=None, **kw):
    params = {'signature': good, 'timestamp': ts, 'nonce': nonce}
    params.update(query_extra or {})
    return call(query=params, **kw)


forged = {'Event': 'retail_pay_notify', 'out_trade_no': 'P_UNIT_1', 'pay_status': 'ORDER_PAY_SUCC'}
r = call(body=forged)
check('匿名伪造通知 → 403', (r.status_code, r.body), (403, b'fail'))
r = call(query={'signature': 'bad', 'timestamp': ts, 'nonce': nonce}, body=forged)
check('错签名 → 403', (r.status_code, r.body), (403, b'fail'))
r = call('GET', query={'signature': good, 'timestamp': ts, 'nonce': nonce, 'echostr': 'echo-ok'})
check('GET URL 校验仍可用', (r.status_code, r.body), (200, b'echo-ok'))
r = call('GET', query={'signature': 'bad', 'timestamp': '1', 'nonce': '1', 'echostr': 'x'})
check('GET 错签名 → 403', r.status_code, 403)
r = call(query={'signature': good, 'timestamp': ts, 'nonce': nonce}, body=forged)
check('正确签名+查无此单 → success', (r.status_code, r.body), (200, b'success'))
r = call(query={'signature': good, 'timestamp': ts, 'nonce': nonce}, body=ValueError('坏报文'))
check('正确签名+报文不可解析 → success 停重试', (r.status_code, r.body), (200, b'success'))
r = call(query={'signature': good, 'timestamp': ts, 'nonce': nonce},
         body={'Event': 'retail_pay_notify', 'out_trade_no': '', 'pay_status': 'ORDER_PAY_SUCC'})
check('缺 out_trade_no → 直接确认收到', (r.status_code, r.body), (200, b'success'))

# ---------- 5. 端到端：验签通过后仍不信任通知体 ----------
print('\n[5] 结算以查单为准（通知体只当信号）')
settled = []


async def spy_settle(db, payment, transaction_id):
    settled.append(transaction_id)


settle_backup = public._settle_successful_payment
public._settle_successful_payment = spy_settle
pay_db = FakeDb(payment=FakePayment())
claim_paid = {'Event': 'retail_pay_notify', 'out_trade_no': 'P_UNIT_1', 'pay_status': 'ORDER_PAY_SUCC'}

try:
    public.query_order = lambda _n: {'pay_status': 'ORDER_PRE_PAY'}
    r = signed(body=claim_paid, db=pay_db)
    check('签了名但查单说未付 → 不结算', (settled, r.status_code, r.body), ([], 502, b'fail'))

    public.query_order = lambda _n: {'pay_status': 'ORDER_PAY_SUCC', 'order_id': 'TX_REAL', 'amount': {'payer_total': 2100}}
    r = signed(body=claim_paid, db=pay_db)
    check('查单确认已付 → 结算且带上微信流水号', (settled, r.status_code), (['TX_REAL'], 200))

    settled.clear()
    public.query_order = lambda _n: {'pay_status': 'ORDER_PAY_SUCC', 'order_id': 'TX_BAD', 'amount': {'payer_total': 1}}
    r = signed(body=claim_paid, db=pay_db)
    check('查单已付但金额对不上 → 不结算待人工', (settled, r.status_code), ([], 502))
finally:
    public._settle_successful_payment = settle_backup
    public.query_order = query_backup

failed = [name for ok, name, *_ in results if not ok]
print(f'\n结果：{len(results) - len(failed)}/{len(results)} 通过')
if failed:
    print('失败：' + ', '.join(failed))
    raise SystemExit(1)
