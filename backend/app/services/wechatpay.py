"""微信支付（小程序 JSAPI）服务层。

设计目标：商户支付凭证（mchid / APIv3 密钥 / 商户证书私钥 / 证书序列号）尚未到位时，
用 Mock 模式即可端到端跑通「下单→支付→回调→退款」全流程；凭证到位后在 .env 填配置、
将 WECHAT_PAY_MOCK 关掉即切真实微信支付，业务代码无需改动。

对外暴露五个能力：
- create_jsapi_payment(payment, openid): 统一下单，返回小程序 uni.requestPayment 所需参数
- query_order(out_trade_no): 主动查单，回调丢失时用它兜底对账
- close_order(out_trade_no): 关闭微信侧预支付单，本地关单时同步调用，避免关单后仍能付款
- verify_and_parse_notify(headers, body): 验签 + 解密支付/退款结果回调
- refund(payment): 按流水原路退款

验签凭证支持微信支付的两种模式（同一商户号二选一，灰度期间可能混用）：
- 微信支付公钥模式：Wechatpay-Serial 携带公钥 ID（PUB_KEY_ID_ 前缀），用本地 pub_key.pem 验签；
- 平台证书模式：Wechatpay-Serial 为平台证书序列号，先从 /v3/certificates 下载平台证书再验签。

金额在数据库以「元」为 Decimal 存储，微信 API 以「分」为整型交互，转换集中在本模块。
"""
from __future__ import annotations

import json
import time
import uuid
from decimal import Decimal, ROUND_HALF_UP
from pathlib import Path

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
    # 公钥模式的公钥ID与公钥文件必须成对配置，否则回调验签无法匹配
    if bool(settings.wechat_pay_public_key_id) != bool(settings.wechat_pay_public_key_path):
        raise HTTPException(
            status_code=500,
            detail='WECHAT_PAY_PUBLIC_KEY_ID and WECHAT_PAY_PUBLIC_KEY_PATH must be configured together',
        )


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
    """校验回调签名并解密报文，返回微信支付/退款结果 dict（含 out_trade_no / transaction_id 等）。

    Mock 模式无平台证书可验，直接把报文当明文结果解析，便于本地联调。
    """
    if is_mock():
        return json.loads(body.decode('utf-8'))
    return _real_verify_and_parse_notify(headers, body)


def query_order(out_trade_no: str) -> dict:
    """主动查单：返回微信支付订单，trade_state=SUCCESS 表示已支付。

    用于回调丢失/延迟时的兜底对账；Mock 模式无真实订单，返回空结果。
    """
    if is_mock():
        return {}
    _ensure_pay_config()
    return _get(f'/v3/pay/transactions/out-trade-no/{out_trade_no}?mchid={settings.wechat_mchid}')


def close_order(out_trade_no: str) -> bool:
    """关闭微信侧预支付单，防止本地关单后用户仍能完成付款。返回是否关闭成功。

    订单不存在、已支付、已关闭等都会返回 False，由调用方决定后续处理。
    """
    if is_mock():
        return True
    _ensure_pay_config()
    try:
        _post(f'/v3/pay/transactions/out-trade-no/{out_trade_no}/close', {'mchid': settings.wechat_mchid})
        return True
    except HTTPException:
        return False


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


def _request(method: str, url_path: str, payload: dict | None = None) -> dict:
    """带商户签名的 v3 请求。url_path 需含查询串（签名内容包含查询串）。"""
    import urllib.error
    import urllib.request

    body = json.dumps(payload, ensure_ascii=False) if payload is not None else ''
    headers = {
        'Content-Type': 'application/json',
        'Accept': 'application/json',
        'Authorization': _authorization_header(method, url_path, body),
    }
    request = urllib.request.Request(
        WECHATPAY_HOST + url_path,
        data=body.encode('utf-8') if payload is not None else None,
        headers=headers,
        method=method,
    )
    try:
        with urllib.request.urlopen(request, timeout=15) as response:
            raw = response.read().decode('utf-8')
    except urllib.error.HTTPError as exc:  # noqa: F821 - urllib.error 随 urllib.request 导入
        detail = exc.read().decode('utf-8', errors='ignore')
        raise HTTPException(status_code=502, detail=f'WeChat Pay API error: {detail}') from exc
    except urllib.error.URLError as exc:
        raise HTTPException(status_code=502, detail=f'WeChat Pay API unreachable: {exc.reason}') from exc
    # 关单等接口成功时返回 204/空体，不能直接 json.loads
    return json.loads(raw) if raw else {}


def _post(url_path: str, payload: dict) -> dict:
    return _request('POST', url_path, payload)


def _get(url_path: str) -> dict:
    return _request('GET', url_path)


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
    _verify_notify_signature(headers, body)
    envelope = json.loads(body.decode('utf-8'))
    resource = envelope.get('resource') or {}
    plaintext = _aes_gcm_decrypt(
        resource.get('associated_data', ''),
        resource.get('nonce', ''),
        resource.get('ciphertext', ''),
    )
    return json.loads(plaintext)


# --------------------------------------------------------------------------
# 验签公钥：优先微信支付公钥（本地读取），回退平台证书（联网下载并缓存）
# --------------------------------------------------------------------------
PLATFORM_CERT_CACHE_SECONDS = 6 * 3600
_platform_certs: dict[str, object] = {}
_platform_certs_expire_at = 0.0
_public_key_cache: object | None = None


def _load_public_key():
    """加载微信支付公钥（pub_key.pem），进程内缓存。公钥长期有效，无需刷新。"""
    global _public_key_cache
    if _public_key_cache is None:
        from cryptography.hazmat.primitives.serialization import load_pem_public_key

        try:
            pem = Path(settings.wechat_pay_public_key_path).read_bytes()
        except OSError as exc:
            raise HTTPException(status_code=500, detail=f'Cannot read WeChat Pay public key: {exc}') from exc
        _public_key_cache = load_pem_public_key(pem)
    return _public_key_cache


def _invalidate_platform_certs() -> None:
    global _platform_certs_expire_at
    _platform_certs.clear()
    _platform_certs_expire_at = 0.0


def _platform_public_keys() -> dict[str, object]:
    """返回 {平台证书序列号: 证书公钥}，带缓存避免每次回调都重新下载。"""
    global _platform_certs_expire_at
    if _platform_certs and time.time() < _platform_certs_expire_at:
        return _platform_certs
    data = _get('/v3/certificates')
    keys: dict[str, object] = {}
    for item in data.get('data') or []:
        encrypted = item.get('encrypt_certificate') or {}
        cert_pem = _aes_gcm_decrypt(
            encrypted.get('associated_data', ''),
            encrypted.get('nonce', ''),
            encrypted.get('ciphertext', ''),
        )
        keys[item.get('serial_no')] = _load_cert_public_key(cert_pem)
    if not keys:
        raise HTTPException(status_code=502, detail='WeChat Pay returned no platform certificate')
    _platform_certs.clear()
    _platform_certs.update(keys)
    _platform_certs_expire_at = time.time() + PLATFORM_CERT_CACHE_SECONDS
    return _platform_certs


def _load_cert_public_key(cert_pem: str):
    from cryptography import x509

    return x509.load_pem_x509_certificate(cert_pem.encode('utf-8')).public_key()


def _notify_header(headers: dict, name: str) -> str:
    for key, value in headers.items():
        if key.lower() == name.lower():
            return value or ''
    return ''


def _public_key_for_serial(serial: str):
    """按 Wechatpay-Serial 取验签公钥：先匹配配置的微信支付公钥 ID，再回退平台证书。

    灰度切换期间微信会按比例随机用公钥或平台证书签名，故两种都保留。
    """
    if settings.wechat_pay_public_key_id and serial == settings.wechat_pay_public_key_id:
        return _load_public_key()
    public_key = _platform_public_keys().get(serial)
    if public_key is None:
        # 序列号未知多为平台证书轮换：清缓存重拉一次再试
        _invalidate_platform_certs()
        public_key = _platform_public_keys().get(serial)
    return public_key


def _verify_notify_signature(headers: dict, body: bytes) -> None:
    """用微信支付公钥或平台证书公钥验 RSA-SHA256 签名，并拒绝超过 5 分钟的回调以防重放。"""
    import base64

    from cryptography.exceptions import InvalidSignature
    from cryptography.hazmat.primitives import hashes
    from cryptography.hazmat.primitives.asymmetric import padding

    timestamp = _notify_header(headers, 'Wechatpay-Timestamp')
    nonce = _notify_header(headers, 'Wechatpay-Nonce')
    signature = _notify_header(headers, 'Wechatpay-Signature')
    serial = _notify_header(headers, 'Wechatpay-Serial')
    if not all([timestamp, nonce, signature, serial]):
        raise HTTPException(status_code=401, detail='WeChat Pay notify missing signature headers')
    try:
        expired = abs(int(time.time()) - int(timestamp)) > 300
    except ValueError as exc:
        raise HTTPException(status_code=401, detail='Invalid WeChat Pay notify timestamp') from exc
    if expired:
        raise HTTPException(status_code=401, detail='WeChat Pay notify timestamp expired')

    public_key = _public_key_for_serial(serial)
    if public_key is None:
        raise HTTPException(status_code=401, detail=f'Unknown WeChat Pay public key id or cert serial: {serial}')

    message = f'{timestamp}\n{nonce}\n{body.decode("utf-8")}\n'
    try:
        public_key.verify(base64.b64decode(signature), message.encode('utf-8'), padding.PKCS1v15(), hashes.SHA256())
    except InvalidSignature as exc:
        raise HTTPException(status_code=401, detail='WeChat Pay notify signature invalid') from exc


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
    if settings.wechat_pay_refund_notify_url:
        payload['notify_url'] = settings.wechat_pay_refund_notify_url
    result = _post(url_path, payload)
    refund_id = result.get('refund_id')
    if not refund_id:
        raise HTTPException(status_code=502, detail='WeChat Pay refund did not return refund_id')
    return {'refund_id': refund_id}
