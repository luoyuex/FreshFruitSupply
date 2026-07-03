import json
from urllib.parse import urlencode
from urllib.request import Request, urlopen

from fastapi import HTTPException

from app.core.config import settings


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


def get_access_token() -> str:
    _ensure_wechat_config()
    query = urlencode({
        'grant_type': 'client_credential',
        'appid': settings.wechat_appid,
        'secret': settings.wechat_secret,
    })
    data = _request_json(f'https://api.weixin.qq.com/cgi-bin/token?{query}')
    if data.get('errcode'):
        raise HTTPException(status_code=400, detail=f"WeChat access_token failed: {data.get('errmsg')}")
    token = data.get('access_token')
    if not token:
        raise HTTPException(status_code=400, detail='WeChat did not return access_token')
    return token
