-- 公告功能：公告表 + 客户的公告已读位
-- 未读 = announcements 中 is_active 且 id 大于 customers.last_read_announcement_id 的记录

CREATE TABLE IF NOT EXISTS announcements (
  id INT AUTO_INCREMENT PRIMARY KEY,
  title VARCHAR(120) NOT NULL,
  content TEXT NOT NULL,
  is_active TINYINT(1) NOT NULL DEFAULT 1,
  created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
  updated_at DATETIME DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
  INDEX ix_announcements_is_active (is_active)
) CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;

-- 客户新增公告已读位（记录读到的最新公告 id）
ALTER TABLE customers
  ADD COLUMN last_read_announcement_id INT NOT NULL DEFAULT 0;
