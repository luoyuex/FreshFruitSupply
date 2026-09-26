-- 场景邮件通知改造：原来只有 orders.email_notify_status 一个标记，只能反映「配货邮件」，
-- 且发信失败后无从重发。改为按通知类型逐条记录投递结果，后台可核对哪一封没送到并手动重发。
--
-- kind: dispatch=新单配货 / updated=改单后的最新明细 / refund_customer=客户自助取消退款 /
--       refund_admin=商户后台退款 / stray_payment=订单关闭后才到账、已原路退回
-- 一个订单每种类型一行（唯一键），重发覆盖状态并累加 attempts。

CREATE TABLE IF NOT EXISTS order_notifications (
  id INT AUTO_INCREMENT PRIMARY KEY,
  order_id INT NOT NULL,
  kind VARCHAR(32) NOT NULL,
  status VARCHAR(16) NOT NULL DEFAULT 'pending',
  attempts INT NOT NULL DEFAULT 0,
  -- 退款类邮件正文里的退款金额：重发时据此还原文案（orders.paid_amount 退款后已清零，不能反推）
  refund_amount DECIMAL(12,2) NULL,
  error TEXT NULL,
  created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
  updated_at DATETIME DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
  sent_at DATETIME NULL,
  UNIQUE KEY uq_order_notifications_order_kind (order_id, kind),
  INDEX ix_order_notifications_kind (kind),
  INDEX ix_order_notifications_status (status),
  CONSTRAINT fk_order_notifications_order_id FOREIGN KEY (order_id) REFERENCES orders(id)
) CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;

-- 存量数据：把历史上的配货邮件投递结果迁成一条 dispatch 记录（表是新建的，不会撞唯一键）
INSERT INTO order_notifications (order_id, kind, status, attempts, sent_at)
SELECT id, 'dispatch', email_notify_status, 1, updated_at
FROM orders
WHERE email_notify_status IN ('sent', 'failed');

-- orders.email_notify_status 保留：语义改为「最近一封场景邮件的状态」，小程序后台仍在读该列
