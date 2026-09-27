-- 已确认订单支持「申请取消 + 商户审核」
--
-- 原来只有商户未确认（待支付/待确认）时用户能自助取消并直接退款；商户已确认（confirmed）
-- 后订单连取消入口都没有，只能联系客服。现在 confirmed 可以提申请，审核通过才退款。
-- 配送中及之后仍然不可取消——货已在路上。
--
-- cancel_request_status: pending=待审核 / approved=已同意（随之退款并置 cancelled）/ rejected=已驳回
-- 驳回后允许再次提交，四个字段整体覆盖为最新一次申请，不保留历史。

ALTER TABLE orders
  ADD COLUMN cancel_request_status VARCHAR(16) NULL AFTER paid_amount,
  ADD COLUMN cancel_request_reason TEXT NULL AFTER cancel_request_status,
  ADD COLUMN cancel_request_note TEXT NULL AFTER cancel_request_reason,
  ADD COLUMN cancel_requested_at DATETIME NULL AFTER cancel_request_note,
  -- 上次取消失败的原因（多为微信退款报错）。取消与退款同事务，失败会整体回滚、状态不变，
  -- 没有这一列的话后台只有一闪而过的 toast，刷新后看不出任何异常，像「点了取消没反应」。
  ADD COLUMN cancel_error TEXT NULL AFTER cancel_requested_at;

CREATE INDEX ix_orders_cancel_request_status ON orders (cancel_request_status);
