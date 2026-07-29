-- 客户提交认证后立即生效；后台仍可取消认证，客户取消后可重新提交。

ALTER TABLE customer_verifications
  MODIFY COLUMN status VARCHAR(32) NOT NULL DEFAULT 'verified';

-- 保存历史待审核客户，后续仅更新和发券给这些客户。
CREATE TEMPORARY TABLE auto_verified_customer_ids (
  customer_id INT PRIMARY KEY,
  verification_id INT NOT NULL
);

INSERT INTO auto_verified_customer_ids (customer_id, verification_id)
SELECT customer_id, MAX(id)
FROM customer_verifications
WHERE status = 'pending_review'
GROUP BY customer_id;

-- 历史待审核申请即时生效，并以最新一份资料更新客户信息。
UPDATE customers AS c
JOIN auto_verified_customer_ids AS a ON a.customer_id = c.id
JOIN customer_verifications AS v ON v.id = a.verification_id
SET c.verification_status = 'verified',
    c.shop_name = v.shop_name,
    c.contact_name = v.contact_name,
    c.business_type = v.business_type;

UPDATE customer_verifications AS v
JOIN auto_verified_customer_ids AS a ON a.customer_id = v.customer_id
SET v.status = 'verified'
WHERE v.status = 'pending_review';

-- 按现有每客户限领规则补发认证券；已有足量券的客户不会重复获得。
INSERT INTO customer_coupons (
  customer_id,
  template_id,
  name,
  description,
  kind,
  amount,
  min_spend,
  status,
  source,
  issued_at,
  expires_at
)
SELECT
  a.customer_id,
  t.id,
  t.name,
  t.description,
  t.kind,
  t.amount,
  t.min_spend,
  'unused',
  'verified',
  NOW(),
  DATE_ADD(NOW(), INTERVAL t.valid_days DAY)
FROM auto_verified_customer_ids AS a
JOIN coupon_templates AS t
  ON t.grant_on_verified = 1
 AND t.is_active = 1
LEFT JOIN (
  SELECT customer_id, template_id, COUNT(*) AS held_count
  FROM customer_coupons
  GROUP BY customer_id, template_id
) AS held
  ON held.customer_id = a.customer_id
 AND held.template_id = t.id
WHERE COALESCE(held.held_count, 0) < t.per_customer_limit;

DROP TEMPORARY TABLE auto_verified_customer_ids;
