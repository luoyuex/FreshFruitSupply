ALTER TABLE admins ADD COLUMN role VARCHAR(32) NOT NULL DEFAULT 'super_admin';
ALTER TABLE admins ADD COLUMN wechat_openid VARCHAR(128) NULL;
ALTER TABLE admins ADD COLUMN nickname VARCHAR(80) NULL;
CREATE UNIQUE INDEX ix_admins_wechat_openid ON admins (wechat_openid);
CREATE INDEX ix_admins_role ON admins (role);
UPDATE admins SET role = 'super_admin' WHERE role IS NULL OR role = '';
