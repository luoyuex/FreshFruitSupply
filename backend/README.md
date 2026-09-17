# Fruit Quote API

FastAPI backend for the fruit quotation mini-program.

## Local setup

```bash
cd backend
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
cp .env.example .env
```

Create a MySQL database, for example:

```sql
CREATE DATABASE fruit_quote CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;
```

Update `DATABASE_URL` in `.env`, then initialize tables and the default admin account:

```bash
python -m app.db.init_db
```

Start the API:

```bash
uvicorn app.main:app --reload
or
uvicorn app.main:app --host 0.0.0.0 --reload

uvicorn app.main:app --host 0.0.0.0 --port 8888 --reload
```

API docs are available at `http://127.0.0.1:8000/docs`.

Default seeded admin account: `admin` / `admin123456`.
Change it before production.

## 微信支付（小程序 JSAPI）

支付链路：`POST /api/orders` 建待支付订单 → `POST /api/orders/{id}/pay` 统一下单并拉起收银台 →
微信回调 `POST /api/payments/wechat/notify` 结算（或前端轮询 `POST /api/orders/{id}/pay/sync` 主动查单兜底）→
取消/超时经 `POST /api/orders/{id}/cancel` 或后台关单原路退款。

### Mock 模式（默认，无需商户凭证）

`WECHAT_PAY_MOCK=true` 时不调用微信，`/api/orders/{id}/pay` 返回带 `mock: true` 的假支付参数，
前端据此调用 `POST /api/payments/dev/mock-success` 模拟支付成功，可端到端联调
「下单 → 支付 → 回调结算 → 退款」全流程。

### 切真实支付前需要准备

1. 微信支付商户号，并完成小程序 appid（`WECHAT_APPID`）与商户号的绑定；
2. 商户 API 证书（`apiclient_key.pem` + 证书序列号），私钥放服务器安全路径，不要提交进仓库；
3. APIv3 密钥；
4. 公网可访问的 HTTPS 回调地址（支付与退款），微信商户平台配置后填入 `WECHAT_PAY_NOTIFY_URL` /
   `WECHAT_PAY_REFUND_NOTIFY_URL`（后者可选，不填则退款按「受理成功」记账）；
5. 把 `.env` 中的 `WECHAT_PAY_MOCK` 改为 `false`，按 `.env.example` 补齐其余支付配置。

回调依赖 `cryptography` 下载并缓存微信平台证书做验签（缓存 6 小时，自动处理证书轮换）。

### 上线前自查

- [ ] `WECHAT_PAY_MOCK=false`，且 `.env` 中支付配置无缺项（缺项时下单支付会返回 500 并提示缺失字段）
- [ ] 回调域名已备案且 HTTPS 可达，`curl` 能打到 `/api/payments/wechat/notify`
- [ ] 真机下单 → 支付 → 订单状态自动从 `unpaid` 变为 `pending`（可对照 `order_payments.status=success`）
- [ ] 在微信里关掉页面不付，等待超时后确认订单 `closed`，且微信侧预支付单已关闭（用户无法再付款）
- [ ] 已付款订单取消 → `order_payments.status=refunded`，微信商户平台可见退款单
- [ ] `order_payments` 中无长期 `pending` 流水（表示回调与查单兜底都工作正常）

### 运维排查

| 现象 | 可能原因 |
| --- | --- |
| 支付成功但订单仍 `unpaid` | 回调未到达（域名/HTTPS/验签失败），前端查单接口会兜底；检查服务日志中 notify 的返回 |
| 回调一直返回 `验签失败` | 平台证书下载失败、`WECHAT_PAY_API_V3_KEY` 错误或系统时间偏差超过 5 分钟 |
| 下单支付报 500 `WeChat Pay is not configured` | `.env` 缺少 `WECHAT_MCHID` / `WECHAT_PAY_API_V3_KEY` / 证书序列号 / 私钥路径 / 回调地址 |
| 退款未到账（`refund_failed`） | 用户收款账户异常，需在微信商户平台重新发起退款 |
