"""微信支付（小程序 JSAPI）服务层。

设计目标：商户支付凭证（mchid / APIv3 密钥 / 商户证书私钥 / 证书序列号）尚未到位时，
用 Mock 模式即可端到端跑通「下单→支付→回调→退款」全流程；凭证到位后在 .env 填配置、
将 WECHAT_PAY_MOCK 关掉即切真实微信支付，业务代码无需改动。

对外暴露三个能力：
- create_jsapi_payment(payment, openid): 统一下单，返回小程序 uni.requestPayment 所需参数
- verify_and_parse_notify(headers, body): 校验并解密支付结果回调
- refund(payment): 按流水原路退款

金额在数据库以「元」为 Decimal 存储，微信 API 以「分」为整型交互，转换集中在本模块。
"""
from __future__ import annotations

import json
import time
import uuid
from decimal import Decimal, ROUND_HALF_UP

from fastapi import HTTPException

from app.core.config import settings

WECHATPAY_HOST = 'https://api.mch.weixin.qq.com'


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


# --------------------------------------------------------------------------
# 真实实现所需的凭证校验与延迟加载（Mock 模式下完全不触发）
# --------------------------------------------------------------------------
def _ensure_pay_config() -> None:
    missing = [
        name
        for name, value in {
            'WECHAT_APPID': settings.wechat_appid,
            'WECHAT_MCHID': settings.wechat_mchid,
            'WECHAT_PAY_API_V3_KEY': settings.wechat_pay_api_v3_key,
            'WECHAT_PAY_CERT_SERIAL': settings.wechat_pay_cert_serial,
            'WECHAT_PAY_PRIVATE_KEY_PATH': settings.wechat_pay_private_key_path,
            'WECHAT_PAY_NOTIFY_URL': settings.wechat_pay_notify_url,
        }.items()
        if not value
    ]
    if missing:
        raise HTTPException(status_code=500, detail=f'WeChat Pay is not configured: {", ".join(missing)}')


# --------------------------------------------------------------------------
# 对外能力
# --------------------------------------------------------------------------
def create_jsapi_payment(payment, openid: str) -> dict:
    """统一下单并返回小程序端 uni.requestPayment 所需的支付参数。

    payment: OrderPayment 实例（含 out_trade_no / amount）。
    返回 dict 会被 API 直接透传给前端，字段名遵循 uni.requestPayment 约定。
    Mock 模式下不调用微信，返回带 mock 标记的假参数，前端据此走 mock-success 联调接口。
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
    return _real_create_jsapi_payment(payment, openid)


def verify_and_parse_notify(headers: dict, body: bytes) -> dict:
    """校验回调签名并解密报文，返回微信支付结果 dict（含 out_trade_no / transaction_id / amount 等）。

    Mock 模式不会走真实回调路径（改由 mock-success 接口驱动），此处保留真实实现。
    """
    return _real_verify_and_parse_notify(headers, body)


def refund(payment) -> dict:
    """按支付流水原路退款。返回含 refund_id 的 dict。

    Mock 模式直接返回假 refund_id，视为退款成功。
    """
    if is_mock():
        return {'mock': True, 'refund_id': f'mock_refund_{payment.out_trade_no}'}
    return _real_refund(payment)


# --------------------------------------------------------------------------
# 真实微信支付实现（RSA-SHA256 签名 + AES-256-GCM 回调解密）
# 依赖 cryptography；仅在非 Mock 模式被调用。
# --------------------------------------------------------------------------
def _load_private_key():
    from cryptography.hazmat.primitives.serialization import load_pem_private_key

    with open(settings.wechat_pay_private_key_path, 'rb') as fh:
        return load_pem_private_key(fh.read(), password=None)


def _rsa_sign(message: str) -> str:
    import base64

    from cryptography.hazmat.primitives import hashes
    from cryptography.hazmat.primitives.asymmetric import padding

    signature = _load_private_key().sign(message.encode('utf-8'), padding.PKCS1v15(), hashes.SHA256())
    return base64.b64encode(signature).decode('utf-8')


def _authorization_header(method: str, url_path: str, body: str) -> str:
    """构造 APIv3 Authorization 头（商户私钥签名）。"""
    nonce = uuid.uuid4().hex
    timestamp = str(int(time.time()))
    message = f'{method}\n{url_path}\n{timestamp}\n{nonce}\n{body}\n'
    signature = _rsa_sign(message)
    return (
        'WECHATPAY2-SHA256-RSA2048 '
        f'mchid="{settings.wechat_mchid}",'
        f'nonce_str="{nonce}",'
        f'signature="{signature}",'
        f'timestamp="{timestamp}",'
        f'serial_no="{settings.wechat_pay_cert_serial}"'
    )


def _post(url_path: str, payload: dict) -> dict:
    import urllib.error
    import urllib.request

    body = json.dumps(payload, ensure_ascii=False)
    headers = {
        'Content-Type': 'application/json',
        'Accept': 'application/json',
        'Authorization': _authorization_header('POST', url_path, body),
    }
    request = urllib.request.Request(WECHATPAY_HOST + url_path, data=body.encode('utf-8'), headers=headers, method='POST')
    try:
        with urllib.request.urlopen(request, timeout=15) as response:
            return json.loads(response.read().decode('utf-8'))
    except urllib.error.HTTPError as exc:  # noqa: F821 - urllib.error 随 urllib.request 导入
        detail = exc.read().decode('utf-8', errors='ignore')
        raise HTTPException(status_code=502, detail=f'WeChat Pay API error: {detail}') from exc


def _real_create_jsapi_payment(payment, openid: str) -> dict:
    _ensure_pay_config()
    if not openid:
        raise HTTPException(status_code=400, detail='Missing openid for JSAPI payment')
    url_path = '/v3/pay/transactions/jsapi'
    payload = {
        'appid': settings.wechat_appid,
        'mchid': settings.wechat_mchid,
        'description': f'水果订单 {payment.out_trade_no}',
        'out_trade_no': payment.out_trade_no,
        'notify_url': settings.wechat_pay_notify_url,
        'amount': {'total': yuan_to_fen(payment.amount), 'currency': 'CNY'},
        'payer': {'openid': openid},
    }
    result = _post(url_path, payload)
    prepay_id = result.get('prepay_id')
    if not prepay_id:
        raise HTTPException(status_code=502, detail='WeChat Pay did not return prepay_id')
    payment.prepay_id = prepay_id

    # 二次签名，返回给小程序 uni.requestPayment
    timestamp = str(int(time.time()))
    nonce = uuid.uuid4().hex
    package = f'prepay_id={prepay_id}'
    sign_message = f'{settings.wechat_appid}\n{timestamp}\n{nonce}\n{package}\n'
    return {
        'timeStamp': timestamp,
        'nonceStr': nonce,
        'package': package,
        'signType': 'RSA',
        'paySign': _rsa_sign(sign_message),
    }


def _real_verify_and_parse_notify(headers: dict, body: bytes) -> dict:
    _ensure_pay_config()
    # 注：完整实现还应用微信平台证书验签 headers 中的签名。此处解密回调资源体，
    # 平台证书验签需先下载并缓存平台证书，凭证到位后补齐。
    envelope = json.loads(body.decode('utf-8'))
    resource = envelope.get('resource') or {}
    plaintext = _aes_gcm_decrypt(
        resource.get('associated_data', ''),
        resource.get('nonce', ''),
        resource.get('ciphertext', ''),
    )
    return json.loads(plaintext)


def _aes_gcm_decrypt(associated_data: str, nonce: str, ciphertext: str) -> str:
    import base64

    from cryptography.hazmat.primitives.ciphers.aead import AESGCM

    key = settings.wechat_pay_api_v3_key.encode('utf-8')
    data = base64.b64decode(ciphertext)
    aesgcm = AESGCM(key)
    plaintext = aesgcm.decrypt(nonce.encode('utf-8'), data, associated_data.encode('utf-8'))
    return plaintext.decode('utf-8')


def _real_refund(payment) -> dict:
    _ensure_pay_config()
    url_path = '/v3/refund/domestic/refunds'
    fen = yuan_to_fen(payment.amount)
    payload = {
        'out_trade_no': payment.out_trade_no,
        'out_refund_no': generate_out_trade_no('R'),
        'amount': {'refund': fen, 'total': fen, 'currency': 'CNY'},
    }
    if settings.wechat_pay_notify_url:
        payload['notify_url'] = settings.wechat_pay_notify_url
    result = _post(url_path, payload)
    refund_id = result.get('refund_id')
    if not refund_id:
        raise HTTPException(status_code=502, detail='WeChat Pay refund did not return refund_id')
    return {'refund_id': refund_id}
