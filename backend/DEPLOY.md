# 服务端部署方案

面向单台 Linux 服务器（Ubuntu 22.04/24.04）部署本项目的后端，域名 `https://zhenguolian.cn`，
接口前缀 `/api`，含微信支付回调与安全加固。

## 架构

```
小程序 / 微信支付服务器
      │ HTTPS
   ┌──▼──────────────────────────┐
   │ nginx (443)                 │  仅对外开放 22/80/443
   │  /api      → 127.0.0.1:8000 │
   │  /uploads  → 静态文件        │
   └──┬──────────────────────────┘
      │ 仅本机回环
   ┌──▼──────────────┐   ┌──────────────┐
   │ uvicorn (1 进程) │──▶│ MySQL 本地    │
   │ systemd 守护     │   │ 非 root 账号  │
   └─────────────────┘   └──────────────┘
```

| 组件 | 位置 |
| --- | --- |
| 代码 | `/srv/fruitquote`（属主 `fruitapp`） |
| 配置 | `/srv/fruitquote/backend/.env`（600） |
| 支付私钥 | `/srv/fruitquote/backend/certs/apiclient_key.pem`（600） |
| 上传文件 | `/srv/fruitquote/backend/uploads` |
| systemd 单元 | `/etc/systemd/system/fruitquote.service` |
| nginx 站点 | `/etc/nginx/conf.d/zhenguolian.conf` |
| 备份 | `/var/backups/fruit` |

---

## 一、服务器基线

```bash
# 1. 建专用账号，应用绝不用 root 跑
sudo adduser --system --group --home /srv/fruitquote fruitapp

# 2. 防火墙：只放行必要端口
sudo ufw default deny incoming
sudo ufw allow 22,80,443/tcp
sudo ufw enable

# 3. SSH 加固：禁用密码登录与 root 登录
sudo sed -i 's/^#\?PasswordAuthentication.*/PasswordAuthentication no/;s/^#\?PermitRootLogin.*/PermitRootLogin no/' /etc/ssh/sshd_config
sudo systemctl restart ssh

# 4. 防爆破 + 自动安全更新
sudo apt install -y fail2ban unattended-upgrades
sudo systemctl enable --now fail2ban

# 5. 时间同步
# 微信回调会校验请求时间戳偏差不超过 5 分钟，时间不准会导致验签全部失败
sudo timedatectl set-ntp true
timedatectl status   # 需看到 NTP synchronized: yes
```

---

## 二、MySQL 加固

```sql
-- 专用账号 + 最小权限，不与 root 共用
CREATE DATABASE fruit_quote CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;
CREATE USER 'fruitapp'@'127.0.0.1' IDENTIFIED BY '强随机密码';
GRANT SELECT, INSERT, UPDATE, DELETE, CREATE, ALTER, INDEX, REFERENCES
  ON fruit_quote.* TO 'fruitapp'@'127.0.0.1';
FLUSH PRIVILEGES;
```

- `my.cnf` 确认 `bind-address = 127.0.0.1`，3306 不对外暴露
- `mysql_secure_installation` 走一遍，删除匿名账号与 test 库
- `.env` 的 `DATABASE_URL` 使用 `fruitapp`，不要用 root

初始化表结构与默认数据（首次部署）：

```bash
cd /srv/fruitquote/backend
sudo -u fruitapp .venv/bin/python -m app.db.init_db
```

---

## 三、后端部署（systemd）

```bash
sudo mkdir -p /srv/fruitquote && sudo chown fruitapp:fruitapp /srv/fruitquote

# 用部署密钥 clone，不要用个人账号密码
sudo -u fruitapp git clone <repo-url> /srv/fruitquote

sudo -u fruitapp python3 -m venv /srv/fruitquote/backend/.venv
sudo -u fruitapp /srv/fruitquote/backend/.venv/bin/pip install -r /srv/fruitquote/backend/requirements.txt
```

### 配置与私钥权限

```bash
# .env 含数据库密码、JWT 密钥、支付配置，必须 600
sudo -u fruitapp install -m 600 /srv/fruitquote/backend/.env.example /srv/fruitquote/backend/.env
sudo -u fruitapp vi /srv/fruitquote/backend/.env

# 支付私钥与公钥单独存放，600 权限
sudo -u fruitapp mkdir -m 700 /srv/fruitquote/backend/certs
sudo -u fruitapp install -m 600 apiclient_key.pem /srv/fruitquote/backend/certs/
sudo -u fruitapp install -m 600 pub_key.pem /srv/fruitquote/backend/certs/
```

### systemd 单元

`/etc/systemd/system/fruitquote.service`：

```ini
[Unit]
Description=Fruit Quote API
After=network-online.target mysql.service
Wants=network-online.target

[Service]
Type=simple
User=fruitapp
Group=fruitapp
WorkingDirectory=/srv/fruitquote/backend
Environment=PYTHONUNBUFFERED=1
# 只监听回环，外部流量一律经 nginx；--workers 1 的原因见下方警告
ExecStart=/srv/fruitquote/backend/.venv/bin/uvicorn app.main:app \
  --host 127.0.0.1 --port 8000 \
  --proxy-headers --forwarded-allow-ips 127.0.0.1 \
  --workers 1
Restart=always
RestartSec=3
NoNewPrivileges=true
PrivateTmp=true
ProtectSystem=full
ProtectHome=true
ReadWritePaths=/srv/fruitquote/backend/uploads

[Install]
WantedBy=multi-user.target
```

```bash
sudo systemctl daemon-reload
sudo systemctl enable --now fruitquote
curl -fsS http://127.0.0.1:8000/health    # {"status":"ok"}
```

### 必须 `--workers 1`

超时关单任务是应用启动时在 `app/main.py` 的 lifespan 中拉起的**进程内后台任务**
（见 `app/services/order_maintenance.py`），且查单、退款没有跨进程加锁。

**开多个 worker = 多个关单任务并发处理同一批订单**，会导致重复关单、重复释放优惠券；
取消订单的退款路径甚至存在重复退款风险。

单进程 + 异步足够支撑本项目体量。若将来要扩容到多 worker，必须先把关单任务改为
外部 `systemd timer` / cron 单点调用，不能保留进程内任务。

---

## 四、nginx 与 HTTPS

```bash
sudo apt install -y nginx certbot python3-certbot-nginx
sudo certbot --nginx -d zhenguolian.cn    # 签发证书并自动配置续期定时器
```

`/etc/nginx/conf.d/zhenguolian.conf`：

```nginx
# 登录接口限速，防密码爆破
limit_req_zone $binary_remote_addr zone=api_login:10m rate=10r/m;

server {
    listen 80;
    server_name zhenguolian.cn;
    location /.well-known/acme-challenge/ { root /var/www/certbot; }
    location / { return 301 https://$host$request_uri; }
}

server {
    listen 443 ssl;
    http2 on;
    server_name zhenguolian.cn;

    ssl_certificate     /etc/letsencrypt/live/zhenguolian.cn/fullchain.pem;
    ssl_certificate_key /etc/letsencrypt/live/zhenguolian.cn/privkey.pem;
    ssl_protocols TLSv1.2 TLSv1.3;
    ssl_session_cache shared:SSL:10m;
    add_header Strict-Transport-Security "max-age=31536000" always;
    add_header X-Content-Type-Options nosniff always;

    client_max_body_size 20m;

    # ===== 微信支付回调：精确匹配、绝不重定向、绝不改写请求体 =====
    location = /api/payments/wechat/notify {
        proxy_pass http://127.0.0.1:8000;
        proxy_set_header Host $host;
        proxy_set_header X-Forwarded-Proto $scheme;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_read_timeout 20s;      # 首次回调会拉取微信平台证书，给足时间
        proxy_buffering off;         # 原样透传请求体与响应
        access_log /var/log/nginx/wechatpay-notify.log;
    }

    location = /api/payments/wechat/refund-notify {
        proxy_pass http://127.0.0.1:8000;
        proxy_set_header Host $host;
        proxy_set_header X-Forwarded-Proto $scheme;
        proxy_read_timeout 20s;
        proxy_buffering off;
        access_log /var/log/nginx/wechatpay-notify.log;
    }

    # 后台登录限速
    location = /api/login {
        limit_req zone=api_login burst=5 nodelay;
        proxy_pass http://127.0.0.1:8000;
        include proxy_params;
    }

    location /api/ {
        proxy_pass http://127.0.0.1:8000;   # 无末尾斜杠：原样保留 /api 前缀
        proxy_set_header Host $host;
        proxy_set_header X-Forwarded-Proto $scheme;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
    }

    # 上传图片交 nginx 直接发，不经 Python
    location /uploads/ {
        alias /srv/fruitquote/backend/uploads/;
        expires 7d;
        add_header Cache-Control "public";
    }

    # 生产环境关闭接口文档
    location ~ ^/(docs|redoc|openapi\.json) { deny all; }

    location / { return 404; }
}
```

### 回调相关的注意事项

- 回调路径**不要**加鉴权、IP 白名单、rewrite；安全性由平台证书验签保证
- 不要用 `$request_body` 之类重建请求体，会破坏签名
- 若前面挂了 CDN / WAF（阿里云 WAF、Cloudflare 等）：放行该路径 POST，关闭人机验证与 JS 挑战，
  并确保响应体不被改写（被改写微信会认为回调失败）
- 回调地址结尾不要带斜杠，必须与 `.env` 中 `WECHAT_PAY_NOTIFY_URL` 完全一致

---

## 五、`.env` 生产必改项

| 配置 | 生产值 | 原因 |
| --- | --- | --- |
| `DATABASE_URL` | `fruitapp` 账号，非 root | 最小权限 |
| `JWT_SECRET_KEY` | 随机 64 位 | 默认值为占位串，可被伪造令牌；修改后存量令牌失效，用户需重新登录 |
| `CORS_ORIGINS` | `https://zhenguolian.cn` | 代码默认值为 `*`，过宽 |
| `PUBLIC_BASE_URL` | `https://zhenguolian.cn` | 对外资源地址 |
| `WECHAT_PAY_MOCK` | `false` | 否则 `/api/payments/dev/mock-success` 可被用于模拟支付（代码内已按 Mock 开关拦截，但不应依赖） |
| `WECHAT_PAY_PRIVATE_KEY_PATH` | `/srv/fruitquote/backend/certs/apiclient_key.pem` | 绝对路径，600 权限 |
| `WECHAT_PAY_PUBLIC_KEY_PATH` | `/srv/fruitquote/backend/certs/pub_key.pem` | 微信支付公钥，回调验签用，与公钥 ID 成对配置 |
| `WECHAT_PAY_PUBLIC_KEY_ID` | `PUB_KEY_ID_0114xxx` | 公钥 ID，商户平台可查 |
| `WECHAT_PAY_NOTIFY_URL` | `https://zhenguolian.cn/api/payments/wechat/notify` | 支付回调 |
| `WECHAT_PAY_REFUND_NOTIFY_URL` | `https://zhenguolian.cn/api/payments/wechat/refund-notify` | 退款回调 |
| `SMTP_*` / `ORDER_NOTIFY_EMAIL` | 生产邮箱 | 五类场景邮件（新单配货 / 改单 / 客户取消退款 / 后台退款 / 关单后到账退回）统一发给这一个地址；`SMTP_USERNAME` 与 `SMTP_PASSWORD`（QQ 邮箱为授权码）任一为空时全部邮件会记为 failed |

### 管理员默认密码必须修改

当前代码没有改密接口，直接更新哈希值：

```bash
cd /srv/fruitquote/backend
sudo -u fruitapp .venv/bin/python -c "from app.core.security import hash_password; print(hash_password('你的新强密码'))"
```

```sql
UPDATE admins SET password_hash = '<上一步输出>' WHERE username = 'admin';
```

---

## 六、备份与恢复

```bash
sudo mkdir -p /var/backups/fruit && sudo chown fruitapp:fruitapp /var/backups/fruit

# 凭据放 600 的 ~/.my.cnf，避免密码出现在 cron 与 ps 中
sudo -u fruitapp bash -c "printf '[mysqldump]\nuser=fruitapp\npassword=强随机密码\n' > ~/.my.cnf && chmod 600 ~/.my.cnf"
```

`crontab -e`（`fruitapp` 用户）：

```cron
# 每日 3:10 全库备份（--single-transaction 不锁表，无需停服）
10 3 * * * mysqldump --single-transaction --default-character-set=utf8mb4 fruit_quote | gzip > /var/backups/fruit/db-$(date +\%F).sql.gz

# 每日 3:30 备份上传图片
30 3 * * * rsync -a --delete /srv/fruitquote/backend/uploads/ /var/backups/fruit/uploads/

# 保留 14 天
40 3 * * * find /var/backups/fruit -mtime +14 -type f -delete
```

- **异地备份**：再用 ossutil / rclone 把 `/var/backups/fruit` 同步到对象存储，本机磁盘损坏才有救
- **恢复演练**：上线前务必执行一次，能恢复才算备份有效

```bash
gunzip -c /var/backups/fruit/db-2026-09-17.sql.gz | mysql -u fruitapp -p 恢复验证库
```

---

## 七、日志与监控

| 用途 | 位置 / 方式 |
| --- | --- |
| 应用日志 | `journalctl -u fruitquote -f`，占用上限设 `SystemMaxUse=500M` |
| 微信回调日志 | `/var/log/nginx/wechatpay-notify.log`（排查回调问题第一现场） |
| 可用性监控 | 外部 uptime 服务探测 `https://zhenguolian.cn/health` |
| 证书续期 | `systemctl list-timers \| grep certbot` |

业务侧健康检查 SQL：

```sql
-- 应恒为 0；大于 0 说明关单任务未运行或回调异常
SELECT COUNT(*) FROM orders
WHERE status = 'unpaid' AND created_at < NOW() - INTERVAL 20 MINUTE;

-- 退款未到账，需人工去商户平台重新发起退款
SELECT * FROM order_payments WHERE status = 'refund_failed';

-- 长时间 pending 的流水（回调与前端查单兜底都没生效）
SELECT * FROM order_payments
WHERE status = 'pending' AND created_at < NOW() - INTERVAL 30 MINUTE;
```

---

## 八、发布与更新流程

```bash
cd /srv/fruitquote
sudo -u fruitapp git pull
sudo -u fruitapp backend/.venv/bin/pip install -r backend/requirements.txt

# 手工 SQL 迁移：先备份，再按文件名顺序执行未执行过的脚本
sudo -u fruitapp bash -c 'mysqldump --single-transaction fruit_quote | gzip > /var/backups/fruit/pre-deploy-$(date +%F-%H%M).sql.gz'
mysql -u fruitapp -p fruit_quote < backend/migrations/2026xxxx_xxx.sql

sudo systemctl restart fruitquote
curl -fsS https://zhenguolian.cn/health
sudo systemctl status fruitquote --no-pager
```

> 本项目迁移为手工 SQL、无执行记录表，曾出现过数据库落后多个迁移的情况。
> 建议后续增加 `schema_migrations` 记录表与自动执行未应用迁移的脚本。

---

## 九、上线安全自查清单

- [ ] 应用以 `fruitapp` 非 root 运行，uvicorn 只监听 `127.0.0.1:8000`
- [ ] `--workers 1`（或已把关单任务移出应用进程）
- [ ] 仅 22/80/443 对外开放，3306 未暴露
- [ ] SSH 已禁用密码登录与 root 登录，fail2ban 生效
- [ ] `.env` 权限 600、`apiclient_key.pem` 权限 600、`~/.my.cnf` 权限 600
- [ ] 仓库中不含 `.env` 与 `*.pem`（`git status` 确认）
- [ ] `JWT_SECRET_KEY` 已更换，管理员默认密码已修改
- [ ] `CORS_ORIGINS` 已收窄，`/docs`、`/openapi.json` 已禁止访问
- [ ] `WECHAT_PAY_MOCK=false`
- [ ] NTP 同步正常（`timedatectl` 显示 `NTP synchronized: yes`）
- [ ] 证书自动续期定时器生效
- [ ] 备份 cron 已实际跑过一次，并完成一次恢复演练
- [ ] 回调连通性验证通过（见下）
- [ ] 真机完成一笔真实小额支付，并成功退款

### 回调连通性验证

部署完成后，不必真实下单即可验证链路：

```bash
curl -i -X POST https://zhenguolian.cn/api/payments/wechat/notify \
  -H 'Content-Type: application/json' -d '{}'
```

期望：HTTP 200 + `{"code":"FAIL","message":"验签失败"}`

拿到该结果说明路由已通、外网可达、nginx 未做跳转。若返回 301/302/404/502，先修 nginx 再谈下单。

### 小程序侧配置

- 小程序后台 → 开发管理 → 服务器域名：`request` 合法域名加入 `https://zhenguolian.cn`（不带 `/api`）
- 前端接口地址需按环境区分：本地用内网 IP，生产用 `https://zhenguolian.cn/api`

---

## 十、常见故障

| 现象 | 排查方向 |
| --- | --- |
| 微信回调收不到 | `/var/log/nginx/wechatpay-notify.log` 是否有请求；无则检查 HTTPS 可达性、WAF、URL 是否被重定向 |
| 回调一直"验签失败" | 公钥 ID / 平台证书序列号与微信实际发来的 `Wechatpay-Serial` 不匹配、公钥文件或 APIv3 密钥错误、服务器时间偏差超 5 分钟、nginx 丢失 `Wechatpay-*` 头 |
| 支付成功但订单仍 `unpaid` | 回调未到达，前端查单接口会兜底；若长时间不更新须查回调链路 |
| 下单报 500 `WeChat Pay is not configured` | `.env` 缺 `WECHAT_MCHID` / `WECHAT_PAY_API_V3_KEY` / 证书序列号 / 私钥路径 / 回调地址 |
| `appid 与 mchid 不匹配` | 小程序 appid 未在商户平台绑定 |
| 订单长时间停在 `unpaid` 未关闭 | 关单任务所在进程异常，检查 `systemctl status fruitquote` |