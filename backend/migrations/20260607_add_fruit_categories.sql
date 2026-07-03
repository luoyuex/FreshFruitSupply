CREATE TABLE IF NOT EXISTS fruit_categories (
  id INT AUTO_INCREMENT PRIMARY KEY,
  name VARCHAR(60) NOT NULL UNIQUE,
  sort_order INT NOT NULL DEFAULT 0,
  is_active TINYINT(1) NOT NULL DEFAULT 1,
  created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
  updated_at DATETIME DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
  INDEX ix_fruit_categories_name (name),
  INDEX ix_fruit_categories_sort_order (sort_order),
  INDEX ix_fruit_categories_is_active (is_active)
) CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;

ALTER TABLE fruits ADD COLUMN category_id INT NULL AFTER name;
CREATE INDEX ix_fruits_category_id ON fruits (category_id);
INSERT IGNORE INTO fruit_categories (name, sort_order, is_active)
  SELECT DISTINCT category, 0, 1 FROM fruits WHERE category IS NOT NULL AND category <> '';
UPDATE fruits
  JOIN fruit_categories ON fruit_categories.name = fruits.category
  SET fruits.category_id = fruit_categories.id
  WHERE fruits.category_id IS NULL;
ALTER TABLE fruits ADD CONSTRAINT fk_fruits_category_id FOREIGN KEY (category_id) REFERENCES fruit_categories(id);
