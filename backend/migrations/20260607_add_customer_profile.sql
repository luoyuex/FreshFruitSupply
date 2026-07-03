ALTER TABLE customers ADD COLUMN nickname VARCHAR(80) NULL AFTER wechat_openid;
ALTER TABLE customers ADD COLUMN avatar_url VARCHAR(255) NULL AFTER nickname;
