-- 收货地址增加经纬度字段（地图选点）
ALTER TABLE customer_addresses
  ADD COLUMN latitude DECIMAL(10,7) NULL,
  ADD COLUMN longitude DECIMAL(10,7) NULL;
