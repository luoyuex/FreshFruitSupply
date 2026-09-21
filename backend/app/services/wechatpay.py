"""微信支付（B2b 门店助手 · wx.requestCommonPayment）服务层。

本项目小程序类目为「商家自营-B2b」，微信要求支付走「B2b 门店助手」支付体系，
与标准微信支付 APIv3 完全不同：

- 前端下单：wx.requestCommonPayment（signData 内含订单信息，无服务端 prepay 环节）
- 签名：支付签名 paySig = HMAC-SHA256(AppKey, uri + '&' + body)；用户态签名
  signature = HMAC-SHA256(sessionKey, signData)；均为 hex 小写
- 查单/关单/退款：POST https://api.weixin.qq.com/retail/B2b/*，带 access_token + pay_sig
- 支付/退款结果：小程序「消息推送」机制推 retail_pay_notify / retail_refund_notify 事件
  （在 mp 后台消息推送配置，由 public.py 的 /payments/b2b/notify 接收）

凭证（.env）：WECHAT_PAY_MCHID（门店助手申请的商户号）、WECHAT_PAY_APPKEY（现网）、
WECHAT_PAY_SANDBOX_APPKEY（沙箱，选填）、WECHAT_PAY_ENV（0 现网 / 1 沙箱）。
凭证未到位时用 Mock 模式端到端联调，业务代码无需改动。

对外暴露能力：
- create_common_payment(payment, session_key): 生成 wx.requestCommonPayment 所需参数
- query_order(out_trade_no): 查单，pay_status=ORDER_PAY_SUCC 表示已支付
- close_order(out_trade_no): 关闭待支付订单（仅 ORDER_PRE_PAY 状态可关）
- refund(payment): 按流水原路退款（发起，异步成功以退款通知/查退款为准）

签名注意：signData/请求体的字符串必须与签名时完全一致，序列化统一用 _dumps()。
金额在数据库以「元」为 Decimal 存储，微信 API 以「分」为整型交互，转换集中在本模块。
"""
from __future__ import annotations

import hashlib
import hmac
import json
import time
import uuid
from decimal import Decimal, ROUND_HALF_UP

from fastapi import HTTPException

from app.core.config import settings

WECHAT_API_HOST = 'https://api.weixin.qq.com'


def is_mock() -> bool:
    return settings.wechat_pay_mock


def yuan_to_fen(amount: Decimal) -> int:
    """元转分，四舍五入到整数分，避免浮点误差。"""
    return int((Decimal(amount) * 100).quantize(Decimal('1'), rounding=ROUND_HALF_UP))


def fen_to_yuan(fen: int) -> Decimal:
    return (Decimal(fen) / 100).quantize(Decimal('0.01'), rounding=ROUND_HALF_UP)


def generate_out_trade_no(prefix: str = 'P') -> str:
    """商户订单号：时间戳 + 短随机，全局唯一且长度受控（<=32）。"""
    return f'{prefix}{int(time.time() * 1000)}{uuid.uuid4().hex[:8]}'


def _dumps(payload: dict) -> str:
    """统一序列化：签名与实际发送必须用同一份字符串，故序列化收敛到本函数。"""
    return json.dumps(payload, ensure_ascii=False, separators=(',', ':'))


def _pay_sig(uri: str, body: str) -> str:
    """支付签名：HMAC-SHA256(AppKey, uri + '&' + body)，hex 小写。uri 不带 query。"""
    key = _appkey().encode('utf-8')
    return hmac.new(key, f'{uri}&{body}'.encode('utf-8'), hashlib.sha256).hexdigest()


def _appkey() -> str:
    if settings.wechat_pay_env == 1:
        appkey = settings.wechat_pay_sandbox_appkey
        if not appkey:
            raise HTTPException(status_code=500, detail='WECHAT_PAY_SANDBOX_APPKEY is not configured')
        return appkey
    appkey = settings.wechat_pay_appkey
    if not appkey:
        raise HTTPException(status_code=500, detail='WECHAT_PAY_APPKEY is not configured')
    return appkey


def _ensure_pay_config() -> None:
    # 按当前支付环境校验对应的 AppKey：env=1 用沙箱，env=0 用现网
    missing = [name for name, value in {
        'WECHAT_PAY_MCHID': settings.wechat_pay_mchid,
    }.items() if not value]
    try:
        _appkey()
    except HTTPException as exc:
        missing.append(exc.detail)
    if missing:
        raise HTTPException(status_code=500, detail=f'WeChat Pay is not configured: {", ".join(missing)}')


# --------------------------------------------------------------------------
# 对外能力
# --------------------------------------------------------------------------
def create_common_payment(payment, session_key: str, description: str | None = None) -> dict:
    """生成小程序 wx.requestCommonPayment 所需参数（B2b 微信支付方式）。

    payment: OrderPayment 实例（含 out_trade_no / amount）。
    session_key: 用户最新 wx.login code 换取的会话密钥，用于用户态签名。
    description: 商品描述（用户账单可见），订单管理接入要求填真实商品信息，缺省用流水号。
    返回 {signData, mode, paySig, signature}，前端原样传给 wx.requestCommonPayment。
    Mock 模式下返回带 mock 标记的假参数，前端据此走 mock-success 联调接口。
    """
    if is_mock():
        return {
            'mock': True,
            'out_trade_no': payment.out_trade_no,
            'timeStamp': str(int(time.time())),
            'nonceStr': uuid.uuid4().hex,
            'package': f'prepay_id=mock_{payment.out_trade_no}',
            'signType': 'RSA',
            'paySign': 'mock-sign',
        }
    _ensure_pay_config()
    if not session_key:
        raise HTTPException(status_code=400, detail='Missing session_key for payment signing')

    sign_data = _dumps({
        'mchid': settings.wechat_pay_mchid,
        'out_trade_no': payment.out_trade_no,
        'description': (description or f'水果订单 {payment.out_trade_no}')[:127],
        'amount': {'order_amount': yuan_to_fen(payment.amount), 'currency': 'CNY'},
        'env': settings.wechat_pay_env,
    })
    return {
        'signData': sign_data,
        'mode': 'retail_pay_goods',
        'paySig': _pay_sig('requestCommonPayment', sign_data),
        'signature': hmac.new(
            session_key.encode('utf-8'),
            sign_data.encode('utf-8'),
            hashlib.sha256,
        ).hexdigest(),
    }


def query_order(out_trade_no: str) -> dict:
    """主动查单：返回 B2b 订单，pay_status=ORDER_PAY_SUCC 表示已支付。

    用于支付通知丢失/延迟时的兜底对账；Mock 模式无真实订单，返回空结果。
    """
    if is_mock():
        return {}
    _ensure_pay_config()
    return _b2b_post('/retail/B2b/getorder', {'mchid': settings.wechat_pay_mchid, 'out_trade_no': out_trade_no})


def close_order(out_trade_no: str) -> bool:
    """关闭待支付订单（仅 ORDER_PRE_PAY 状态可关），防止关单后仍能付款。返回是否成功。"""
    if is_mock():
        return True
    _ensure_pay_config()
    try:
        _b2b_post('/retail/B2b/closeb2border', {'mchid': settings.wechat_pay_mchid, 'out_trade_no': out_trade_no})
        return True
    except HTTPException:
        return False


def refund(payment) -> dict:
    """按支付流水原路退款（160 天内；同单退款间隔须大于 1 分钟）。

    仅发起退款请求，成功与否以退款通知（retail_refund_notify）或查退款为准。
    Mock 模式直接返回假 refund_id，视为退款成功。
    """
    if is_mock():
        return {'mock': True, 'refund_id': f'mock_refund_{payment.out_trade_no}'}
    _ensure_pay_config()
    result = _b2b_post('/retail/B2b/refund', {
        'mchid': settings.wechat_pay_mchid,
        'out_trade_no': payment.out_trade_no,
        'out_refund_no': generate_out_trade_no('R'),
        'refund_amount': yuan_to_fen(payment.amount),
        'refund_from': 1,  # 人工客服退款
        'description': '订单取消退款',
    })
    refund_id = result.get('refund_id')
    if not refund_id:
        raise HTTPException(status_code=502, detail='WeChat B2b refund did not return refund_id')
    return {'refund_id': refund_id}


# --------------------------------------------------------------------------
# retail/B2b 服务器 API：access_token + pay_sig 双重鉴权
# --------------------------------------------------------------------------
def _b2b_post(url_path: str, payload: dict) -> dict:
    """调用 api.weixin.qq.com/retail/B2b/* 服务器接口。

    url_path 形如 /retail/B2b/getorder；pay_sig 对「不带 query 的 uri + 请求体」计算，
    access_token 以 query 传入、不参与签名。
    """
    import urllib.error
    import urllib.parse
    import urllib.request

    from app.services.wechat import get_access_token

    body = _dumps(payload)
    query = urllib.parse.urlencode({
        'access_token': get_access_token(),
        'pay_sig': _pay_sig(url_path, body),
    })
    request = urllib.request.Request(
        WECHAT_API_HOST + url_path + '?' + query,
        data=body.encode('utf-8'),
        headers={'Content-Type': 'application/json'},
        method='POST',
    )
    try:
        with urllib.request.urlopen(request, timeout=15) as response:
            raw = response.read().decode('utf-8')
    except urllib.error.HTTPError as exc:  # noqa: F821 - urllib.error 随 urllib.request 导入
        detail = exc.read().decode('utf-8', errors='ignore')
        raise HTTPException(status_code=502, detail=f'WeChat B2b API error: {detail}') from exc
    except urllib.error.URLError as exc:
        raise HTTPException(status_code=502, detail=f'WeChat B2b API unreachable: {exc.reason}') from exc
    result = json.loads(raw) if raw else {}
    errcode = result.get('errcode')
    if errcode not in (None, 0):
        # 9403201 订单不存在等业务性失败，交由调用方按失败处理
        raise HTTPException(status_code=502, detail=f'WeChat B2b API error {errcode}: {result.get("errmsg")}')
    return result
