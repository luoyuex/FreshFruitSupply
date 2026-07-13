from decimal import Decimal, InvalidOperation

from sqlalchemy.orm import Session

from app.models import SystemSetting

# 配送费相关设置的键名与默认值。默认门槛 120 元、配送费 10 元，
# 与产品初始约定一致；后台可随时改，改动即时对新提交/修改的订单生效。
DELIVERY_FREE_THRESHOLD_KEY = 'delivery_free_threshold'
DELIVERY_FEE_KEY = 'delivery_fee'

DEFAULT_DELIVERY_FREE_THRESHOLD = Decimal('120')
DEFAULT_DELIVERY_FEE = Decimal('10')


def get_setting(db: Session, key: str) -> str | None:
    row = db.query(SystemSetting).filter(SystemSetting.key == key).first()
    return row.value if row else None


def set_setting(db: Session, key: str, value: str) -> SystemSetting:
    row = db.query(SystemSetting).filter(SystemSetting.key == key).first()
    if row:
        row.value = value
    else:
        row = SystemSetting(key=key, value=value)
        db.add(row)
    return row


def _decimal_setting(db: Session, key: str, default: Decimal) -> Decimal:
    raw = get_setting(db, key)
    if raw is None:
        return default
    try:
        value = Decimal(str(raw))
    except (InvalidOperation, ValueError):
        return default
    return value if value >= 0 else default


def get_delivery_config(db: Session) -> tuple[Decimal, Decimal]:
    """返回 (包邮门槛, 配送费)。缺失或非法时回退默认值。"""
    threshold = _decimal_setting(db, DELIVERY_FREE_THRESHOLD_KEY, DEFAULT_DELIVERY_FREE_THRESHOLD)
    fee = _decimal_setting(db, DELIVERY_FEE_KEY, DEFAULT_DELIVERY_FEE)
    return threshold, fee


def compute_delivery_fee(goods_total: Decimal, threshold: Decimal, fee: Decimal) -> Decimal:
    """商品原价合计达到（含等于）门槛则包邮，否则收取配送费。

    门槛按商品原价合计判断（不扣券），与前端展示口径一致。
    """
    goods_total = Decimal(goods_total)
    if goods_total >= threshold:
        return Decimal('0')
    return fee
