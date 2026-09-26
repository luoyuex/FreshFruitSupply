"""重置后台管理员密码（Web 后台与小程序后台共用同一套 admins 账号）。

用法（服务器上按 DEPLOY.md 的方式执行）：
  只看现有账号：        sudo -u fruitapp .venv/bin/python reset_admin_password.py
  重置某个账号的密码：  sudo -u fruitapp .venv/bin/python reset_admin_password.py <username> '<新密码>'

安全约定：不带参数时只读、不改任何数据；账号不存在时不新建、不修改；
新密码不落日志也不回显。重置只影响密码校验，不会使已签发的登录令牌失效
（小程序端已有的后台会话仍可继续使用）。
"""
import sys

from app.core.security import hash_password
from app.db.session import SessionLocal
from app.models import Admin

MIN_PASSWORD_LENGTH = 6


def list_accounts(db) -> None:
    rows = db.query(Admin).order_by(Admin.id.asc()).all()
    if not rows:
        print('  （库里还没有管理员账号）')
        return
    for item in rows:
        print(f'  id={item.id:<4} username={item.username:<18} role={item.role or "-":<13} '
              f'启用={item.is_active} 昵称={item.nickname or "-"} '
              f'openid={item.wechat_openid or "未绑定（该账号无法从个人中心进入后台）"}')


def main(argv: list[str]) -> int:
    if len(argv) < 3:
        db = SessionLocal()
        try:
            print('当前后台账号（不含密码）：')
            list_accounts(db)
            print('\n重置密码：python reset_admin_password.py <username> \'<新密码>\'')
        finally:
            db.close()
        return 0

    username, password = argv[1], argv[2]
    if len(password) < MIN_PASSWORD_LENGTH:
        print(f'密码至少 {MIN_PASSWORD_LENGTH} 位，未做任何修改')
        return 1

    db = SessionLocal()
    try:
        admin = db.query(Admin).filter(Admin.username == username).first()
        if not admin:
            print(f'账号 {username} 不存在，未做任何修改。现有账号：')
            list_accounts(db)
            return 1
        admin.password_hash = hash_password(password)
        db.commit()
        print(f'已重置 {username} 的密码（角色 {admin.role}、启用状态 {admin.is_active} 未改动）')
        print('现在可用该账号登录 Web 后台；若账号已停用，请先在后台用户管理里启用或用有权限的账号操作。')
        return 0
    finally:
        db.close()


if __name__ == '__main__':
    raise SystemExit(main(sys.argv))
