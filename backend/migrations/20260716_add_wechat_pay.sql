-- 微信支付改造：从「预定制（下单即完成、无需支付）」改为「先付款后下单成立」
-- 订单状态新增 unpaid（待支付，下单初始态）、closed（超时未付自动关闭）；
-- pending 语义调整为「已付款待供应商确认」，cancelled 语义调整为「已付款后取消（已退款）」。
--
-- 一个订单可能有多笔交易（首付 + 加商品补差价），故独立建支付流水表 order_payments。
-- orders.paid_amount 记录已成功支付累计，payable_total 为应付，二者差额即需补款金额。

ALTER TABLE orders
  ADD COLUMN paid_amount DECIMAL(12,2) NOT NULL DEFAULT 0;

CREATE TABLE IF NOT EXISTS order_payments (
  id INT AUTO_INCREMENT PRIMARY KEY,
  order_id INT NOT NULL,
  out_trade_no VARCHAR(64) NOT NULL,
  -- initial=首付；supplement=加商品补差价
  kind VARCHAR(16) NOT NULL DEFAULT 'initial',
  amount DECIMAL(12,2) NOT NULL DEFAULT 0,
  -- pending=待支付；success=支付成功；refunded=已退款；cancelled=作废未支付的补差价流水
  status VARCHAR(16) NOT NULL DEFAULT 'pending',
  prepay_id VARCHAR(128) NULL,
  transaction_id VARCHAR(64) NULL,
  refund_id VARCHAR(64) NULL,
  -- 补差价流水暂存变更后的订单明细快照（JSON），支付成功回调后才落库到订单
  pending_payload TEXT NULL,
  created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
  updated_at DATETIME DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
  paid_at DATETIME NULL,
  refunded_at DATETIME NULL,
  UNIQUE KEY uq_order_payments_out_trade_no (out_trade_no),
  INDEX ix_order_payments_order_id (order_id),
  INDEX ix_order_payments_status (status),
  INDEX ix_order_payments_transaction_id (transaction_id),
  CONSTRAINT fk_order_payments_order_id FOREIGN KEY (order_id) REFERENCES orders(id)
) CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;

-- 存量订单：视为已付款并已确认，保持 pending 语义不受影响，已付金额回填为应付。
UPDATE orders SET paid_amount = payable_total WHERE paid_amount = 0 AND payable_total > 0;
