-- 配送费功能：订单新增配送费列，并写入可后台配置的包邮门槛/配送费默认值
-- 配送费按商品原价合计判断门槛（低于门槛收费，达到则包邮），作为独立一行计入实付。

ALTER TABLE orders
  ADD COLUMN delivery_fee DECIMAL(12,2) NOT NULL DEFAULT 0;

-- 包邮门槛与配送费存于通用 system_settings（键值表），后台可随时调整。
-- 默认：满 120 元包邮，否则收 10 元。
INSERT INTO system_settings (`key`, `value`, created_at, updated_at)
VALUES
  ('delivery_free_threshold', '120', CURRENT_TIMESTAMP, CURRENT_TIMESTAMP),
  ('delivery_fee', '10', CURRENT_TIMESTAMP, CURRENT_TIMESTAMP)
ON DUPLICATE KEY UPDATE `key` = `key`;
