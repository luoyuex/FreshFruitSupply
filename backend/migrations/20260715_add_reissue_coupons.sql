-- 商品补送券：给卡券体系加 kind 维度
-- discount=满减券（现有，有金额/门槛，每单限一张，参与实付抵扣）
-- reissue=商品补送券（无金额，配货标记，可与满减券及多张补送券叠加，只手动发放）
-- 存量券默认 discount，行为完全不变。

ALTER TABLE coupon_templates
  ADD COLUMN kind VARCHAR(16) NOT NULL DEFAULT 'discount';
ALTER TABLE coupon_templates
  ADD INDEX ix_coupon_templates_kind (kind);

ALTER TABLE customer_coupons
  ADD COLUMN kind VARCHAR(16) NOT NULL DEFAULT 'discount';
ALTER TABLE customer_coupons
  ADD INDEX ix_customer_coupons_kind (kind);

-- 补送券快照券种备注（补送内容说明），模板后续改动不影响已发出的券
ALTER TABLE customer_coupons
  ADD COLUMN description TEXT NULL;
