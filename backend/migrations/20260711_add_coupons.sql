-- 红包/卡券功能：券模板、用户券实例，以及订单上的券字段
-- 说明：orders.coupon_id 与 customer_coupons.order_id 之间为普通整型列（非外键），
--       以避免两表循环外键，跨表关联由应用层维护。

CREATE TABLE IF NOT EXISTS coupon_templates (
  id INT AUTO_INCREMENT PRIMARY KEY,
  name VARCHAR(80) NOT NULL,
  description TEXT NULL,
  discount_type VARCHAR(16) NOT NULL DEFAULT 'amount',
  amount DECIMAL(10,2) NOT NULL DEFAULT 0,
  min_spend DECIMAL(12,2) NOT NULL DEFAULT 0,
  valid_days INT NOT NULL DEFAULT 30,
  grant_on_verified TINYINT(1) NOT NULL DEFAULT 0,
  per_customer_limit INT NOT NULL DEFAULT 1,
  is_active TINYINT(1) NOT NULL DEFAULT 1,
  created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
  updated_at DATETIME DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
  INDEX ix_coupon_templates_grant_on_verified (grant_on_verified),
  INDEX ix_coupon_templates_is_active (is_active)
) CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;

CREATE TABLE IF NOT EXISTS customer_coupons (
  id INT AUTO_INCREMENT PRIMARY KEY,
  customer_id INT NOT NULL,
  template_id INT NOT NULL,
  name VARCHAR(80) NOT NULL,
  amount DECIMAL(10,2) NOT NULL,
  min_spend DECIMAL(12,2) NOT NULL DEFAULT 0,
  status VARCHAR(16) NOT NULL DEFAULT 'unused',
  source VARCHAR(16) NOT NULL DEFAULT 'verified',
  issued_at DATETIME DEFAULT CURRENT_TIMESTAMP,
  expires_at DATETIME NOT NULL,
  used_at DATETIME NULL,
  order_id INT NULL,
  created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
  updated_at DATETIME DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
  INDEX ix_customer_coupons_customer_id (customer_id),
  INDEX ix_customer_coupons_template_id (template_id),
  INDEX ix_customer_coupons_status (status),
  INDEX ix_customer_coupons_expires_at (expires_at),
  INDEX ix_customer_coupons_order_id (order_id),
  CONSTRAINT fk_customer_coupons_customer_id FOREIGN KEY (customer_id) REFERENCES customers(id),
  CONSTRAINT fk_customer_coupons_template_id FOREIGN KEY (template_id) REFERENCES coupon_templates(id)
) CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;

ALTER TABLE orders
  ADD COLUMN coupon_id INT NULL,
  ADD COLUMN discount_amount DECIMAL(12,2) NOT NULL DEFAULT 0,
  ADD COLUMN payable_total DECIMAL(12,2) NOT NULL DEFAULT 0;

ALTER TABLE orders ADD INDEX ix_orders_coupon_id (coupon_id);

-- 历史订单回填：无券订单实付 = 商品原价合计
UPDATE orders SET payable_total = estimated_total WHERE payable_total = 0;
