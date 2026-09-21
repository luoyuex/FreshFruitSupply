from functools import lru_cache
from pathlib import Path
from pydantic import field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    app_name: str = 'Fruit Quote API'
    api_prefix: str = '/api'
    database_url: str = 'mysql+pymysql://root:password@127.0.0.1:3306/fruit_quote?charset=utf8mb4'
    jwt_secret_key: str = 'change-me-before-production'
    jwt_algorithm: str = 'HS256'
    jwt_expire_minutes: int = 43200  # 30 days — mini-program users shouldn't need frequent re-login
    jwt_refresh_grace_minutes: int = 43200  # 过期后仍可刷新的宽限期
    upload_dir: Path = Path('uploads')
    public_base_url: str = 'http://127.0.0.1:8000'
    cors_origins: str = '*'
    smtp_host: str = ''
    smtp_port: int = 465
    smtp_username: str = ''
    smtp_password: str = ''
    smtp_from: str = ''
    order_notify_email: str = ''
    wechat_appid: str = ''
    wechat_secret: str = ''
    # 微信支付（B2b 门店助手 · wx.requestCommonPayment）：
    # 商户号为门店助手-支付管理申请的商户号；签名用 AppKey（HMAC），不使用 APIv3 密钥/证书
    wechat_pay_mchid: str = ''
    wechat_pay_env: int = 0  # 0 现网 / 1 沙箱（沙箱仅开发版/体验版可用，正式版必须 0）
    wechat_pay_appkey: str = ''
    wechat_pay_sandbox_appkey: str = ''
    # 小程序「消息推送」配置的 Token：用于支付/退款通知（retail_pay_notify 等）验签与 URL 校验
    wechat_b2b_msg_token: str = ''
    # Mock 模式：不调用真实微信支付 API，用开发接口模拟支付成功，便于凭证到位前联调
    wechat_pay_mock: bool = True
    # 待支付订单超时自动关闭时长（分钟）
    order_unpaid_timeout_minutes: int = 15
    # 店铺认证功能开关：关闭时 C 端隐藏认证入口、计价一律走普通价、提交认证接口返回 403。
    # 快速上线验证期关闭；后续放开改 .env 即可，前端经 /api/config/client 自动感知、无需发版
    verification_enabled: bool = True

    model_config = SettingsConfigDict(env_file='.env', env_file_encoding='utf-8', extra='ignore')

    @field_validator('database_url')
    @classmethod
    def require_mysql(cls, value: str) -> str:
        if not value.startswith('mysql+pymysql://'):
            raise ValueError('DATABASE_URL must use mysql+pymysql://')
        return value

    @property
    def upload_root(self) -> Path:
        return self.upload_dir if self.upload_dir.is_absolute() else Path.cwd() / self.upload_dir

    @property
    def cors_origin_list(self) -> list[str]:
        return [item.strip() for item in self.cors_origins.split(',') if item.strip()] or ['*']


@lru_cache
def get_settings() -> Settings:
    return Settings()


settings = get_settings()
