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
    jwt_expire_minutes: int = 10080
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
    # 微信支付（小程序 JSAPI）商户配置；未配齐时配合 wechat_pay_mock 走模拟支付
    wechat_mchid: str = ''
    wechat_pay_api_v3_key: str = ''
    wechat_pay_cert_serial: str = ''
    wechat_pay_private_key_path: str = ''
    wechat_pay_notify_url: str = ''
    # Mock 模式：不调用真实微信支付 API，用开发接口模拟支付成功，便于凭证到位前联调
    wechat_pay_mock: bool = True
    # 待支付订单超时自动关闭时长（分钟）
    order_unpaid_timeout_minutes: int = 15

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
