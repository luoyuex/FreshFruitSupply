import json
import time
from urllib.parse import urlencode
from urllib.request import Request, urlopen

from fastapi import HTTPException

from app.core.config import settings

# access_token 进程内缓存：官方限额内避免每次支付查单都刷新 token
_access_token_cache: str = ''
_access_token_expire_at: float = 0.0


def _request_json(url: str, method: str = 'GET', payload: dict | None = None) -> dict:
    data = None
    headers = {'Content-Type': 'application/json'}
    if payload is not None:
        data = json.dumps(payload, ensure_ascii=False).encode('utf-8')
    request = Request(url, data=data, headers=headers, method=method)
    with urlopen(request, timeout=10) as response:
        return json.loads(response.read().decode('utf-8'))


def _ensure_wechat_config() -> None:
    if not settings.wechat_appid or not settings.wechat_secret:
        raise HTTPException(status_code=500, detail='WeChat appid/secret is not configured')


def code_to_session(code: str) -> dict:
    _ensure_wechat_config()
    query = urlencode({
        'appid': settings.wechat_appid,
        'secret': settings.wechat_secret,
        'js_code': code,
        'grant_type': 'authorization_code',
    })
    data = _request_json(f'https://api.weixin.qq.com/sns/jscode2session?{query}')
    if data.get('errcode'):
        raise HTTPException(status_code=400, detail=f"WeChat login failed: {data.get('errmsg')}")
    if not data.get('openid'):
        raise HTTPException(status_code=400, detail='WeChat login did not return openid')
    return data


def get_access_token(force_refresh: bool = False) -> str:
    """获取小程序接口调用凭证，带进程内缓存（提前 5 分钟过期）。

    使用 stable_token 接口：微信侧集中管理 token，多实例/多环境（本地联调 + 服务器）
    共用同一 appid 时取到的是同一个 token，不会像旧 /cgi-bin/token 那样互相挤掉线。
    """
    global _access_token_cache, _access_token_expire_at
    if not force_refresh and _access_token_cache and time.time() < _access_token_expire_at:
        return _access_token_cache
    _ensure_wechat_config()
    data = _request_json('https://api.weixin.qq.com/cgi-bin/stable_token', method='POST', payload={
        'grant_type': 'client_credential',
        'appid': settings.wechat_appid,
        'secret': settings.wechat_secret,
        'force_refresh': force_refresh,
    })
    if data.get('errcode'):
        raise HTTPException(status_code=400, detail=f"WeChat access_token failed: {data.get('errmsg')}")
    token = data.get('access_token')
    if not token:
        raise HTTPException(status_code=400, detail='WeChat did not return access_token')
    _access_token_cache = token
    _access_token_expire_at = time.time() + max(60, int(data.get('expires_in', 7200)) - 300)
    return token
