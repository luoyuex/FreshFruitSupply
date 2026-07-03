CREATE TABLE IF NOT EXISTS customer_addresses (
  id INT AUTO_INCREMENT PRIMARY KEY,
  customer_id INT NOT NULL,
  receiver_name VARCHAR(60) NOT NULL,
  receiver_phone VARCHAR(32) NOT NULL,
  province VARCHAR(60) NOT NULL,
  city VARCHAR(60) NOT NULL,
  district VARCHAR(60) NOT NULL,
  detail_address VARCHAR(255) NOT NULL,
  delivery_note TEXT NULL,
  is_default TINYINT(1) NOT NULL DEFAULT 0,
  created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
  updated_at DATETIME DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
  INDEX ix_customer_addresses_customer_id (customer_id),
  INDEX ix_customer_addresses_is_default (is_default),
  CONSTRAINT fk_customer_addresses_customer_id FOREIGN KEY (customer_id) REFERENCES customers(id)
) CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;
