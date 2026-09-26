-- 后台账号改造：权限从「两个写死的角色」改成「按模块勾选」，并补上最近登录时间。
--
-- admins.permissions 存 JSON 数组，取值见 app/api/deps.py 的 ALL_PERMISSIONS；
-- 为 NULL 时回落到角色默认权限（super_admin=全部，order_admin=仅订单），存量账号行为不变。
-- 存量账号顺手回填成显式集合，之后在后台改勾选就是纯数据变更，不再受角色影响。

ALTER TABLE admins
  ADD COLUMN permissions VARCHAR(255) NULL AFTER role,
  ADD COLUMN last_login_at DATETIME NULL AFTER permissions;

UPDATE admins SET permissions = '["orders", "verifications", "fruits", "stats", "coupons", "users", "settings"]'
WHERE role = 'super_admin' AND permissions IS NULL;

UPDATE admins SET permissions = '["orders"]'
WHERE role = 'order_admin' AND permissions IS NULL;
