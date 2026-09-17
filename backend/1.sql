-- --------------------------------------------------------
-- 主机:                           127.0.0.1
-- 服务器版本:                        5.7.26 - MySQL Community Server (GPL)
-- 服务器操作系统:                      Win64
-- HeidiSQL 版本:                  11.0.0.5919
-- --------------------------------------------------------

/*!40101 SET @OLD_CHARACTER_SET_CLIENT=@@CHARACTER_SET_CLIENT */;
/*!40101 SET NAMES utf8 */;
/*!50503 SET NAMES utf8mb4 */;
/*!40014 SET @OLD_FOREIGN_KEY_CHECKS=@@FOREIGN_KEY_CHECKS, FOREIGN_KEY_CHECKS=0 */;
/*!40101 SET @OLD_SQL_MODE=@@SQL_MODE, SQL_MODE='NO_AUTO_VALUE_ON_ZERO' */;


-- 导出 fruit_quote 的数据库结构
DROP DATABASE IF EXISTS `fruit_quote`;
CREATE DATABASE IF NOT EXISTS `fruit_quote` /*!40100 DEFAULT CHARACTER SET utf8 COLLATE utf8_unicode_ci */;
USE `fruit_quote`;

-- 导出  表 fruit_quote.admins 结构
DROP TABLE IF EXISTS `admins`;
CREATE TABLE IF NOT EXISTS `admins` (
  `id` int(11) NOT NULL AUTO_INCREMENT,
  `username` varchar(60) COLLATE utf8mb4_unicode_ci NOT NULL,
  `password_hash` varchar(255) COLLATE utf8mb4_unicode_ci NOT NULL,
  `role` varchar(32) COLLATE utf8mb4_unicode_ci NOT NULL,
  `wechat_openid` varchar(128) COLLATE utf8mb4_unicode_ci DEFAULT NULL,
  `nickname` varchar(80) COLLATE utf8mb4_unicode_ci DEFAULT NULL,
  `is_active` tinyint(1) NOT NULL,
  `created_at` datetime NOT NULL DEFAULT CURRENT_TIMESTAMP,
  `updated_at` datetime NOT NULL DEFAULT CURRENT_TIMESTAMP,
  PRIMARY KEY (`id`),
  UNIQUE KEY `ix_admins_username` (`username`),
  UNIQUE KEY `wechat_openid` (`wechat_openid`),
  KEY `ix_admins_role` (`role`),
  KEY `ix_admins_id` (`id`)
) ENGINE=InnoDB AUTO_INCREMENT=4 DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- 正在导出表  fruit_quote.admins 的数据：~3 rows (大约)
/*!40000 ALTER TABLE `admins` DISABLE KEYS */;
INSERT INTO `admins` (`id`, `username`, `password_hash`, `role`, `wechat_openid`, `nickname`, `is_active`, `created_at`, `updated_at`) VALUES
	(1, 'admin', '$2b$12$WcjjKyVWqKNjlyI.lmypd.85s3mUFg7vFuevIDY5D8QrDNceiHVwa', 'super_admin', 'ogk4Z46pq-KkjQSFzIYJGif7YKww', NULL, 1, '2026-06-27 13:51:24', '2026-06-27 13:51:24'),
	(2, 'miss', '$2b$12$InloJlKw/hbeaP/KXn8yz.xeqm.dIBls6l0Jb4BZ1h36USXF4p2T2', 'super_admin', 'ohAha3Rt5bc6P2zDiQ5iIUNGKT6Q', 'miss', 1, '2026-06-27 18:32:29', '2026-06-27 18:32:29'),
	(3, 'wx3', '$2b$12$TuQVJwUC/BsUBRj90vC2RObA0WKv3fk4siAdrDsnd97JN9nWgV42i', 'super_admin', 'ohAha3QqbluEkVAQdWsc8TALKceA', '1', 1, '2026-06-29 14:54:26', '2026-06-29 14:54:26');
/*!40000 ALTER TABLE `admins` ENABLE KEYS */;

-- 导出  表 fruit_quote.announcements 结构
DROP TABLE IF EXISTS `announcements`;
CREATE TABLE IF NOT EXISTS `announcements` (
  `id` int(11) NOT NULL AUTO_INCREMENT,
  `title` varchar(120) COLLATE utf8mb4_unicode_ci NOT NULL,
  `content` text COLLATE utf8mb4_unicode_ci NOT NULL,
  `is_active` tinyint(1) NOT NULL DEFAULT '1',
  `created_at` datetime DEFAULT CURRENT_TIMESTAMP,
  `updated_at` datetime DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
  PRIMARY KEY (`id`),
  KEY `ix_announcements_is_active` (`is_active`)
) ENGINE=MyISAM DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- 正在导出表  fruit_quote.announcements 的数据：0 rows
/*!40000 ALTER TABLE `announcements` DISABLE KEYS */;
/*!40000 ALTER TABLE `announcements` ENABLE KEYS */;

-- 导出  表 fruit_quote.coupon_templates 结构
DROP TABLE IF EXISTS `coupon_templates`;
CREATE TABLE IF NOT EXISTS `coupon_templates` (
  `id` int(11) NOT NULL AUTO_INCREMENT,
  `name` varchar(80) COLLATE utf8mb4_unicode_ci NOT NULL,
  `description` text COLLATE utf8mb4_unicode_ci,
  `discount_type` varchar(16) COLLATE utf8mb4_unicode_ci NOT NULL DEFAULT 'amount',
  `amount` decimal(10,2) NOT NULL DEFAULT '0.00',
  `min_spend` decimal(12,2) NOT NULL DEFAULT '0.00',
  `valid_days` int(11) NOT NULL DEFAULT '30',
  `grant_on_verified` tinyint(1) NOT NULL DEFAULT '0',
  `per_customer_limit` int(11) NOT NULL DEFAULT '1',
  `is_active` tinyint(1) NOT NULL DEFAULT '1',
  `created_at` datetime DEFAULT CURRENT_TIMESTAMP,
  `updated_at` datetime DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
  `kind` varchar(16) COLLATE utf8mb4_unicode_ci NOT NULL DEFAULT 'discount',
  PRIMARY KEY (`id`),
  KEY `ix_coupon_templates_grant_on_verified` (`grant_on_verified`),
  KEY `ix_coupon_templates_is_active` (`is_active`),
  KEY `ix_coupon_templates_kind` (`kind`)
) ENGINE=MyISAM DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- 正在导出表  fruit_quote.coupon_templates 的数据：0 rows
/*!40000 ALTER TABLE `coupon_templates` DISABLE KEYS */;
/*!40000 ALTER TABLE `coupon_templates` ENABLE KEYS */;

-- 导出  表 fruit_quote.customers 结构
DROP TABLE IF EXISTS `customers`;
CREATE TABLE IF NOT EXISTS `customers` (
  `id` int(11) NOT NULL AUTO_INCREMENT,
  `phone` varchar(32) COLLATE utf8mb4_unicode_ci NOT NULL,
  `wechat_openid` varchar(128) COLLATE utf8mb4_unicode_ci DEFAULT NULL,
  `nickname` varchar(80) COLLATE utf8mb4_unicode_ci DEFAULT NULL,
  `avatar_url` varchar(255) COLLATE utf8mb4_unicode_ci DEFAULT NULL,
  `verification_status` varchar(32) COLLATE utf8mb4_unicode_ci NOT NULL,
  `shop_name` varchar(120) COLLATE utf8mb4_unicode_ci DEFAULT NULL,
  `contact_name` varchar(60) COLLATE utf8mb4_unicode_ci DEFAULT NULL,
  `business_type` varchar(80) COLLATE utf8mb4_unicode_ci DEFAULT NULL,
  `created_at` datetime NOT NULL DEFAULT CURRENT_TIMESTAMP,
  `updated_at` datetime NOT NULL DEFAULT CURRENT_TIMESTAMP,
  `last_read_announcement_id` int(11) NOT NULL DEFAULT '0',
  PRIMARY KEY (`id`),
  UNIQUE KEY `ix_customers_phone` (`phone`),
  UNIQUE KEY `wechat_openid` (`wechat_openid`),
  KEY `ix_customers_verification_status` (`verification_status`),
  KEY `ix_customers_id` (`id`)
) ENGINE=InnoDB AUTO_INCREMENT=15 DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- 正在导出表  fruit_quote.customers 的数据：~14 rows (大约)
/*!40000 ALTER TABLE `customers` DISABLE KEYS */;
INSERT INTO `customers` (`id`, `phone`, `wechat_openid`, `nickname`, `avatar_url`, `verification_status`, `shop_name`, `contact_name`, `business_type`, `created_at`, `updated_at`, `last_read_announcement_id`) VALUES
	(1, 'wx:ogk4Z46pq-KkjQSFzIYJGif7YKww', 'ogk4Z46pq-KkjQSFzIYJGif7YKww', NULL, NULL, 'unverified', NULL, NULL, NULL, '2026-06-27 13:59:27', '2026-06-27 13:59:27', 0),
	(2, '423', 'ohAha3Rt5bc6P2zDiQ5iIUNGKT6Q', 'miss', '/uploads/customer-avatars/1ba1965552544a8698cc9f9a74d51f8f.jpg', 'verified', '234', '324', '24', '2026-06-27 18:27:34', '2026-06-30 15:51:38', 0),
	(3, 'wx:ohAha3QqbluEkVAQdWsc8TALKceA', 'ohAha3QqbluEkVAQdWsc8TALKceA', '1', NULL, 'unverified', NULL, '', NULL, '2026-06-28 19:57:44', '2026-06-29 14:53:59', 0),
	(4, 'wx:ohAha3ZngG-RdF0sLMC4uM19_15I', 'ohAha3ZngG-RdF0sLMC4uM19_15I', NULL, NULL, 'unverified', NULL, NULL, NULL, '2026-06-29 17:55:29', '2026-06-29 17:55:29', 0),
	(5, 'wx:ohAha3dAlVX3agcX_MvTmjvc8Lp0', 'ohAha3dAlVX3agcX_MvTmjvc8Lp0', NULL, NULL, 'unverified', NULL, NULL, NULL, '2026-06-29 17:55:30', '2026-06-29 17:55:30', 0),
	(6, 'wx:ohAha3VkPF_SbotZmxFxydZdyFOI', 'ohAha3VkPF_SbotZmxFxydZdyFOI', NULL, NULL, 'unverified', NULL, NULL, NULL, '2026-06-29 17:55:36', '2026-06-29 17:55:36', 0),
	(7, 'wx:ohAha3fTxO6oY_MbywtS04PqE1BI', 'ohAha3fTxO6oY_MbywtS04PqE1BI', 't', NULL, 'unverified', NULL, '', NULL, '2026-06-30 15:06:21', '2026-06-30 15:06:33', 0),
	(8, '15070511241', 'ohAha3duFg73lsofpd7-PWjCpfRw', NULL, NULL, 'verified', 'missblue', 'x', '蛋糕店', '2026-06-30 15:19:47', '2026-06-30 15:22:06', 0),
	(9, 'wx:ohAha3dHSH-SPMJFx5Uu1uE7VA9k', 'ohAha3dHSH-SPMJFx5Uu1uE7VA9k', NULL, NULL, 'unverified', NULL, NULL, NULL, '2026-06-30 15:55:35', '2026-06-30 15:55:35', 0),
	(10, 'wx:ohAha3UeskLg1vCn6NP_5EAoNGUU', 'ohAha3UeskLg1vCn6NP_5EAoNGUU', NULL, NULL, 'unverified', NULL, NULL, NULL, '2026-06-30 16:00:42', '2026-06-30 16:00:42', 0),
	(11, 'wx:ohAha3RIm0KWMfHiIFEbmnofdHh8', 'ohAha3RIm0KWMfHiIFEbmnofdHh8', NULL, NULL, 'unverified', NULL, NULL, NULL, '2026-06-30 18:23:14', '2026-06-30 18:23:14', 0),
	(12, 'wx:ohAha3VKf5INGGTwrI-Otp8M_120', 'ohAha3VKf5INGGTwrI-Otp8M_120', NULL, NULL, 'unverified', NULL, NULL, NULL, '2026-07-01 12:04:56', '2026-07-01 12:04:56', 0),
	(13, 'wx:ohAha3Ukmt_ZKppsHK30Th6WV394', 'ohAha3Ukmt_ZKppsHK30Th6WV394', NULL, NULL, 'unverified', NULL, NULL, NULL, '2026-07-01 12:05:02', '2026-07-01 12:05:02', 0),
	(14, 'wx:ohAha3TACyUtoBvWrRyWqSm9sVzQ', 'ohAha3TACyUtoBvWrRyWqSm9sVzQ', NULL, NULL, 'unverified', NULL, NULL, NULL, '2026-09-06 09:43:08', '2026-09-06 09:43:08', 0);
/*!40000 ALTER TABLE `customers` ENABLE KEYS */;

-- 导出  表 fruit_quote.customers_bak20260916 结构
DROP TABLE IF EXISTS `customers_bak20260916`;
CREATE TABLE IF NOT EXISTS `customers_bak20260916` (
  `id` int(11) NOT NULL AUTO_INCREMENT,
  `phone` varchar(32) COLLATE utf8mb4_unicode_ci NOT NULL,
  `wechat_openid` varchar(128) COLLATE utf8mb4_unicode_ci DEFAULT NULL,
  `nickname` varchar(80) COLLATE utf8mb4_unicode_ci DEFAULT NULL,
  `avatar_url` varchar(255) COLLATE utf8mb4_unicode_ci DEFAULT NULL,
  `verification_status` varchar(32) COLLATE utf8mb4_unicode_ci NOT NULL,
  `shop_name` varchar(120) COLLATE utf8mb4_unicode_ci DEFAULT NULL,
  `contact_name` varchar(60) COLLATE utf8mb4_unicode_ci DEFAULT NULL,
  `business_type` varchar(80) COLLATE utf8mb4_unicode_ci DEFAULT NULL,
  `created_at` datetime NOT NULL DEFAULT CURRENT_TIMESTAMP,
  `updated_at` datetime NOT NULL DEFAULT CURRENT_TIMESTAMP,
  PRIMARY KEY (`id`),
  UNIQUE KEY `ix_customers_phone` (`phone`),
  UNIQUE KEY `wechat_openid` (`wechat_openid`),
  KEY `ix_customers_verification_status` (`verification_status`),
  KEY `ix_customers_id` (`id`)
) ENGINE=InnoDB AUTO_INCREMENT=15 DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- 正在导出表  fruit_quote.customers_bak20260916 的数据：~14 rows (大约)
/*!40000 ALTER TABLE `customers_bak20260916` DISABLE KEYS */;
INSERT INTO `customers_bak20260916` (`id`, `phone`, `wechat_openid`, `nickname`, `avatar_url`, `verification_status`, `shop_name`, `contact_name`, `business_type`, `created_at`, `updated_at`) VALUES
	(1, 'wx:ogk4Z46pq-KkjQSFzIYJGif7YKww', 'ogk4Z46pq-KkjQSFzIYJGif7YKww', NULL, NULL, 'unverified', NULL, NULL, NULL, '2026-06-27 13:59:27', '2026-06-27 13:59:27'),
	(2, '423', 'ohAha3Rt5bc6P2zDiQ5iIUNGKT6Q', 'miss', '/uploads/customer-avatars/1ba1965552544a8698cc9f9a74d51f8f.jpg', 'verified', '234', '324', '24', '2026-06-27 18:27:34', '2026-06-30 15:51:38'),
	(3, 'wx:ohAha3QqbluEkVAQdWsc8TALKceA', 'ohAha3QqbluEkVAQdWsc8TALKceA', '1', NULL, 'unverified', NULL, '', NULL, '2026-06-28 19:57:44', '2026-06-29 14:53:59'),
	(4, 'wx:ohAha3ZngG-RdF0sLMC4uM19_15I', 'ohAha3ZngG-RdF0sLMC4uM19_15I', NULL, NULL, 'unverified', NULL, NULL, NULL, '2026-06-29 17:55:29', '2026-06-29 17:55:29'),
	(5, 'wx:ohAha3dAlVX3agcX_MvTmjvc8Lp0', 'ohAha3dAlVX3agcX_MvTmjvc8Lp0', NULL, NULL, 'unverified', NULL, NULL, NULL, '2026-06-29 17:55:30', '2026-06-29 17:55:30'),
	(6, 'wx:ohAha3VkPF_SbotZmxFxydZdyFOI', 'ohAha3VkPF_SbotZmxFxydZdyFOI', NULL, NULL, 'unverified', NULL, NULL, NULL, '2026-06-29 17:55:36', '2026-06-29 17:55:36'),
	(7, 'wx:ohAha3fTxO6oY_MbywtS04PqE1BI', 'ohAha3fTxO6oY_MbywtS04PqE1BI', 't', NULL, 'unverified', NULL, '', NULL, '2026-06-30 15:06:21', '2026-06-30 15:06:33'),
	(8, '15070511241', 'ohAha3duFg73lsofpd7-PWjCpfRw', NULL, NULL, 'verified', 'missblue', 'x', '蛋糕店', '2026-06-30 15:19:47', '2026-06-30 15:22:06'),
	(9, 'wx:ohAha3dHSH-SPMJFx5Uu1uE7VA9k', 'ohAha3dHSH-SPMJFx5Uu1uE7VA9k', NULL, NULL, 'unverified', NULL, NULL, NULL, '2026-06-30 15:55:35', '2026-06-30 15:55:35'),
	(10, 'wx:ohAha3UeskLg1vCn6NP_5EAoNGUU', 'ohAha3UeskLg1vCn6NP_5EAoNGUU', NULL, NULL, 'unverified', NULL, NULL, NULL, '2026-06-30 16:00:42', '2026-06-30 16:00:42'),
	(11, 'wx:ohAha3RIm0KWMfHiIFEbmnofdHh8', 'ohAha3RIm0KWMfHiIFEbmnofdHh8', NULL, NULL, 'unverified', NULL, NULL, NULL, '2026-06-30 18:23:14', '2026-06-30 18:23:14'),
	(12, 'wx:ohAha3VKf5INGGTwrI-Otp8M_120', 'ohAha3VKf5INGGTwrI-Otp8M_120', NULL, NULL, 'unverified', NULL, NULL, NULL, '2026-07-01 12:04:56', '2026-07-01 12:04:56'),
	(13, 'wx:ohAha3Ukmt_ZKppsHK30Th6WV394', 'ohAha3Ukmt_ZKppsHK30Th6WV394', NULL, NULL, 'unverified', NULL, NULL, NULL, '2026-07-01 12:05:02', '2026-07-01 12:05:02'),
	(14, 'wx:ohAha3TACyUtoBvWrRyWqSm9sVzQ', 'ohAha3TACyUtoBvWrRyWqSm9sVzQ', NULL, NULL, 'unverified', NULL, NULL, NULL, '2026-09-06 09:43:08', '2026-09-06 09:43:08');
/*!40000 ALTER TABLE `customers_bak20260916` ENABLE KEYS */;

-- 导出  表 fruit_quote.customer_addresses 结构
DROP TABLE IF EXISTS `customer_addresses`;
CREATE TABLE IF NOT EXISTS `customer_addresses` (
  `id` int(11) NOT NULL AUTO_INCREMENT,
  `customer_id` int(11) NOT NULL,
  `receiver_name` varchar(60) COLLATE utf8mb4_unicode_ci NOT NULL,
  `receiver_phone` varchar(32) COLLATE utf8mb4_unicode_ci NOT NULL,
  `province` varchar(60) COLLATE utf8mb4_unicode_ci NOT NULL,
  `city` varchar(60) COLLATE utf8mb4_unicode_ci NOT NULL,
  `district` varchar(60) COLLATE utf8mb4_unicode_ci NOT NULL,
  `detail_address` varchar(255) COLLATE utf8mb4_unicode_ci NOT NULL,
  `delivery_note` text COLLATE utf8mb4_unicode_ci,
  `is_default` tinyint(1) NOT NULL,
  `created_at` datetime NOT NULL DEFAULT CURRENT_TIMESTAMP,
  `updated_at` datetime NOT NULL DEFAULT CURRENT_TIMESTAMP,
  `latitude` decimal(10,7) DEFAULT NULL,
  `longitude` decimal(10,7) DEFAULT NULL,
  PRIMARY KEY (`id`),
  KEY `ix_customer_addresses_is_default` (`is_default`),
  KEY `ix_customer_addresses_id` (`id`),
  KEY `ix_customer_addresses_customer_id` (`customer_id`),
  CONSTRAINT `customer_addresses_ibfk_1` FOREIGN KEY (`customer_id`) REFERENCES `customers` (`id`)
) ENGINE=InnoDB AUTO_INCREMENT=3 DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- 正在导出表  fruit_quote.customer_addresses 的数据：~2 rows (大约)
/*!40000 ALTER TABLE `customer_addresses` DISABLE KEYS */;
INSERT INTO `customer_addresses` (`id`, `customer_id`, `receiver_name`, `receiver_phone`, `province`, `city`, `district`, `detail_address`, `delivery_note`, `is_default`, `created_at`, `updated_at`, `latitude`, `longitude`) VALUES
	(1, 2, '谢', '15770511044', '上海', '上海', '松江区', '文亭苑425弄', '', 1, '2026-07-10 15:03:35', '2026-07-10 15:03:35', NULL, NULL),
	(2, 14, '冯绍峰', '15117889024', '高大上', '大概是', '梵蒂冈', '刚发的', '', 1, '2026-09-06 09:43:34', '2026-09-06 09:43:34', NULL, NULL);
/*!40000 ALTER TABLE `customer_addresses` ENABLE KEYS */;

-- 导出  表 fruit_quote.customer_coupons 结构
DROP TABLE IF EXISTS `customer_coupons`;
CREATE TABLE IF NOT EXISTS `customer_coupons` (
  `id` int(11) NOT NULL AUTO_INCREMENT,
  `customer_id` int(11) NOT NULL,
  `template_id` int(11) NOT NULL,
  `name` varchar(80) COLLATE utf8mb4_unicode_ci NOT NULL,
  `amount` decimal(10,2) NOT NULL,
  `min_spend` decimal(12,2) NOT NULL DEFAULT '0.00',
  `status` varchar(16) COLLATE utf8mb4_unicode_ci NOT NULL DEFAULT 'unused',
  `source` varchar(16) COLLATE utf8mb4_unicode_ci NOT NULL DEFAULT 'verified',
  `issued_at` datetime DEFAULT CURRENT_TIMESTAMP,
  `expires_at` datetime NOT NULL,
  `used_at` datetime DEFAULT NULL,
  `order_id` int(11) DEFAULT NULL,
  `created_at` datetime DEFAULT CURRENT_TIMESTAMP,
  `updated_at` datetime DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
  `kind` varchar(16) COLLATE utf8mb4_unicode_ci NOT NULL DEFAULT 'discount',
  `description` text COLLATE utf8mb4_unicode_ci,
  PRIMARY KEY (`id`),
  KEY `ix_customer_coupons_customer_id` (`customer_id`),
  KEY `ix_customer_coupons_template_id` (`template_id`),
  KEY `ix_customer_coupons_status` (`status`),
  KEY `ix_customer_coupons_expires_at` (`expires_at`),
  KEY `ix_customer_coupons_order_id` (`order_id`),
  KEY `ix_customer_coupons_kind` (`kind`)
) ENGINE=MyISAM DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- 正在导出表  fruit_quote.customer_coupons 的数据：0 rows
/*!40000 ALTER TABLE `customer_coupons` DISABLE KEYS */;
/*!40000 ALTER TABLE `customer_coupons` ENABLE KEYS */;

-- 导出  表 fruit_quote.customer_verifications 结构
DROP TABLE IF EXISTS `customer_verifications`;
CREATE TABLE IF NOT EXISTS `customer_verifications` (
  `id` int(11) NOT NULL AUTO_INCREMENT,
  `customer_id` int(11) NOT NULL,
  `shop_name` varchar(120) COLLATE utf8mb4_unicode_ci NOT NULL,
  `contact_name` varchar(60) COLLATE utf8mb4_unicode_ci NOT NULL,
  `phone` varchar(32) COLLATE utf8mb4_unicode_ci NOT NULL,
  `business_type` varchar(80) COLLATE utf8mb4_unicode_ci NOT NULL,
  `image_urls` text COLLATE utf8mb4_unicode_ci NOT NULL,
  `status` varchar(32) COLLATE utf8mb4_unicode_ci NOT NULL DEFAULT 'verified',
  `review_note` text COLLATE utf8mb4_unicode_ci,
  `created_at` datetime NOT NULL DEFAULT CURRENT_TIMESTAMP,
  `updated_at` datetime NOT NULL DEFAULT CURRENT_TIMESTAMP,
  PRIMARY KEY (`id`),
  KEY `ix_customer_verifications_phone` (`phone`),
  KEY `ix_customer_verifications_status` (`status`),
  KEY `ix_customer_verifications_id` (`id`),
  KEY `ix_customer_verifications_customer_id` (`customer_id`),
  CONSTRAINT `customer_verifications_ibfk_1` FOREIGN KEY (`customer_id`) REFERENCES `customers` (`id`)
) ENGINE=InnoDB AUTO_INCREMENT=3 DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- 正在导出表  fruit_quote.customer_verifications 的数据：~2 rows (大约)
/*!40000 ALTER TABLE `customer_verifications` DISABLE KEYS */;
INSERT INTO `customer_verifications` (`id`, `customer_id`, `shop_name`, `contact_name`, `phone`, `business_type`, `image_urls`, `status`, `review_note`, `created_at`, `updated_at`) VALUES
	(1, 8, 'missblue', 'x', '15070511241', '蛋糕店', '["/uploads/customer-verifications/d29ef9a00bcb4ae1ad1ded730c131e7b.jpg"]', 'verified', NULL, '2026-06-30 15:21:14', '2026-06-30 15:22:06'),
	(2, 2, '234', '324', '423', '24', '["/uploads/customer-verifications/3879912cfadd4bdba59dea14287848b9.jpg"]', 'verified', NULL, '2026-06-30 15:51:15', '2026-06-30 15:51:38');
/*!40000 ALTER TABLE `customer_verifications` ENABLE KEYS */;

-- 导出  表 fruit_quote.customer_verifications_bak20260916 结构
DROP TABLE IF EXISTS `customer_verifications_bak20260916`;
CREATE TABLE IF NOT EXISTS `customer_verifications_bak20260916` (
  `id` int(11) NOT NULL AUTO_INCREMENT,
  `customer_id` int(11) NOT NULL,
  `shop_name` varchar(120) COLLATE utf8mb4_unicode_ci NOT NULL,
  `contact_name` varchar(60) COLLATE utf8mb4_unicode_ci NOT NULL,
  `phone` varchar(32) COLLATE utf8mb4_unicode_ci NOT NULL,
  `business_type` varchar(80) COLLATE utf8mb4_unicode_ci NOT NULL,
  `image_urls` text COLLATE utf8mb4_unicode_ci NOT NULL,
  `status` varchar(32) COLLATE utf8mb4_unicode_ci NOT NULL,
  `review_note` text COLLATE utf8mb4_unicode_ci,
  `created_at` datetime NOT NULL DEFAULT CURRENT_TIMESTAMP,
  `updated_at` datetime NOT NULL DEFAULT CURRENT_TIMESTAMP,
  PRIMARY KEY (`id`),
  KEY `ix_customer_verifications_phone` (`phone`),
  KEY `ix_customer_verifications_status` (`status`),
  KEY `ix_customer_verifications_id` (`id`),
  KEY `ix_customer_verifications_customer_id` (`customer_id`)
) ENGINE=InnoDB AUTO_INCREMENT=3 DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- 正在导出表  fruit_quote.customer_verifications_bak20260916 的数据：~2 rows (大约)
/*!40000 ALTER TABLE `customer_verifications_bak20260916` DISABLE KEYS */;
INSERT INTO `customer_verifications_bak20260916` (`id`, `customer_id`, `shop_name`, `contact_name`, `phone`, `business_type`, `image_urls`, `status`, `review_note`, `created_at`, `updated_at`) VALUES
	(1, 8, 'missblue', 'x', '15070511241', '蛋糕店', '["/uploads/customer-verifications/d29ef9a00bcb4ae1ad1ded730c131e7b.jpg"]', 'verified', NULL, '2026-06-30 15:21:14', '2026-06-30 15:22:06'),
	(2, 2, '234', '324', '423', '24', '["/uploads/customer-verifications/3879912cfadd4bdba59dea14287848b9.jpg"]', 'verified', NULL, '2026-06-30 15:51:15', '2026-06-30 15:51:38');
/*!40000 ALTER TABLE `customer_verifications_bak20260916` ENABLE KEYS */;

-- 导出  表 fruit_quote.fruits 结构
DROP TABLE IF EXISTS `fruits`;
CREATE TABLE IF NOT EXISTS `fruits` (
  `id` int(11) NOT NULL AUTO_INCREMENT,
  `name` varchar(80) COLLATE utf8mb4_unicode_ci NOT NULL,
  `category_id` int(11) DEFAULT NULL,
  `category` varchar(60) COLLATE utf8mb4_unicode_ci NOT NULL,
  `image_url` varchar(255) COLLATE utf8mb4_unicode_ci DEFAULT NULL,
  `image_urls_json` text COLLATE utf8mb4_unicode_ci,
  `detail_image_urls_json` text COLLATE utf8mb4_unicode_ci,
  `origin` varchar(120) COLLATE utf8mb4_unicode_ci DEFAULT NULL,
  `spec` varchar(120) COLLATE utf8mb4_unicode_ci NOT NULL,
  `unit` varchar(20) COLLATE utf8mb4_unicode_ci NOT NULL,
  `stock_status` varchar(32) COLLATE utf8mb4_unicode_ci NOT NULL,
  `is_recommended` tinyint(1) NOT NULL,
  `created_at` datetime NOT NULL DEFAULT CURRENT_TIMESTAMP,
  `updated_at` datetime NOT NULL DEFAULT CURRENT_TIMESTAMP,
  PRIMARY KEY (`id`),
  KEY `ix_fruits_category_id` (`category_id`),
  KEY `ix_fruits_id` (`id`),
  KEY `ix_fruits_name` (`name`),
  KEY `ix_fruits_stock_status` (`stock_status`),
  KEY `ix_fruits_category` (`category`),
  CONSTRAINT `fruits_ibfk_1` FOREIGN KEY (`category_id`) REFERENCES `fruit_categories` (`id`)
) ENGINE=InnoDB AUTO_INCREMENT=37 DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- 正在导出表  fruit_quote.fruits 的数据：~36 rows (大约)
/*!40000 ALTER TABLE `fruits` DISABLE KEYS */;
INSERT INTO `fruits` (`id`, `name`, `category_id`, `category`, `image_url`, `image_urls_json`, `detail_image_urls_json`, `origin`, `spec`, `unit`, `stock_status`, `is_recommended`, `created_at`, `updated_at`) VALUES
	(1, '西瓜', 7, '瓜类', '/uploads/fruit-images/aab4dae2d77543c5abc9a07c905f1d3f.jpg', '["/uploads/fruit-images/aab4dae2d77543c5abc9a07c905f1d3f.jpg"]', '[]', '', '个', '斤', 'in_stock', 1, '2026-06-27 14:08:07', '2026-06-28 14:19:20'),
	(2, '妃子笑荔枝', 1, '应季水果', '/uploads/fruit-images/86cc110ba0f44c8cb14b7bfaa0dca9ce.webp', '["/uploads/fruit-images/86cc110ba0f44c8cb14b7bfaa0dca9ce.webp"]', '[]', '', '斤', '斤', 'in_stock', 1, '2026-06-27 14:12:33', '2026-06-27 14:12:33'),
	(3, '一级大青芒', 2, '芒果', '/uploads/fruit-images/bc90681ae2de458792d3e83993f67315.jpg', '["/uploads/fruit-images/bc90681ae2de458792d3e83993f67315.jpg"]', '["/uploads/fruit-images/f98290d4a78841889c0742c3d3f57566.jpg"]', '', '件', '斤', 'in_stock', 1, '2026-06-27 14:14:56', '2026-06-29 15:11:57'),
	(4, '水仙', 2, '芒果', '/uploads/fruit-images/02a40af9b05b40cc917af6537bbf0a73.webp', '["/uploads/fruit-images/02a40af9b05b40cc917af6537bbf0a73.webp"]', '["/uploads/fruit-images/5064743801564a489aff4e8b51873e2a.jpg"]', '', '斤', '斤', 'in_stock', 1, '2026-06-27 14:19:59', '2026-06-29 14:59:11'),
	(5, '阳光玫瑰', 3, '葡提', '/uploads/fruit-images/ce84f9d9e0c942b48256f705e53f5fe5.jpg', '["/uploads/fruit-images/ce84f9d9e0c942b48256f705e53f5fe5.jpg"]', '["/uploads/fruit-images/5b359b47a17f4eaaa9bbe01c18c69748.jpg"]', '', '斤', '斤', 'in_stock', 0, '2026-06-28 14:10:30', '2026-06-29 15:05:29'),
	(6, '进口火龙果', 4, '火龙果', '/uploads/fruit-images/c785b7979c1a48e198e7b10599414275.jpg', '["/uploads/fruit-images/c785b7979c1a48e198e7b10599414275.jpg"]', '["/uploads/fruit-images/df5af5ad3772437d96ae02a361440065.jpg", "/uploads/fruit-images/e5a118c418a84f759a9f861fa5de83f2.jpg"]', '', '箱', '箱', 'in_stock', 0, '2026-06-28 14:11:30', '2026-06-29 15:07:38'),
	(7, '进口火龙果', 4, '火龙果', '/uploads/fruit-images/e5d4658398fc4e7090a6333bfb81ed07.jpg', '["/uploads/fruit-images/e5d4658398fc4e7090a6333bfb81ed07.jpg"]', '["/uploads/fruit-images/898252b2fb5b43039f491303580830eb.jpg", "/uploads/fruit-images/733310a0eca14823ba1e96cd55f8ee06.jpg"]', '', '斤', '斤', 'in_stock', 0, '2026-06-28 14:11:50', '2026-06-29 15:07:26'),
	(8, '橙子', 5, '柑橘橙', '/uploads/fruit-images/394beaae0a644abf91992ab1abd51ab2.jpg', '["/uploads/fruit-images/394beaae0a644abf91992ab1abd51ab2.jpg"]', '["/uploads/fruit-images/519cfa0a68104cecb4d9de12b834e64c.jpg", "/uploads/fruit-images/0b3a065fb86141b7b5876eda0e9d6b4a.jpg"]', '', '斤', '斤', 'in_stock', 0, '2026-06-28 14:13:05', '2026-06-29 15:13:59'),
	(9, '菠萝', 6, '凤梨 | 菠萝', NULL, '[]', '[]', '', '进', '斤', 'out_of_stock', 0, '2026-06-28 14:13:56', '2026-06-29 15:14:28'),
	(10, '芭乐', 1, '应季水果', '/uploads/fruit-images/2d81332466944be0a82d6f3e48ede6ec.jpg', '["/uploads/fruit-images/2d81332466944be0a82d6f3e48ede6ec.jpg"]', '["/uploads/fruit-images/560b0718c8a44374b494a8c29687b2c9.jpg"]', '', '斤', '斤', 'in_stock', 0, '2026-06-28 14:14:27', '2026-06-29 15:02:19'),
	(11, '哈密瓜', 7, '瓜类', '/uploads/fruit-images/e0624f8ab679479eb7108ab0ce35dd98.jpg', '["/uploads/fruit-images/e0624f8ab679479eb7108ab0ce35dd98.jpg"]', '["/uploads/fruit-images/5abcd3b04d8d4313905340425445b9e8.jpg"]', '', '斤', '斤', 'in_stock', 0, '2026-06-28 14:15:15', '2026-06-29 15:15:37'),
	(12, '黑莓', 8, '莓果', '/uploads/fruit-images/11db949886b64448b26dfd7e54335c4a.jpg', '["/uploads/fruit-images/11db949886b64448b26dfd7e54335c4a.jpg"]', '["/uploads/fruit-images/1f9b4243d9a54696a0a5cab375657e58.jpg"]', '', '盒', '盒', 'in_stock', 0, '2026-06-28 14:16:35', '2026-06-29 15:09:46'),
	(13, '红提', 3, '葡提', '/uploads/fruit-images/3ba9329812fe45e7bff6e8543b7aa107.jpg', '["/uploads/fruit-images/3ba9329812fe45e7bff6e8543b7aa107.jpg"]', '["/uploads/fruit-images/b8a3bc0c87004af8aa1ae9d062ed0862.jpg", "/uploads/fruit-images/57150f1c4f874045a8dd6102f5bd5f8a.jpg"]', '', '斤', '斤', 'in_stock', 0, '2026-06-28 14:16:57', '2026-06-29 15:04:08'),
	(14, '凤梨', 6, '凤梨 | 菠萝', '/uploads/fruit-images/a82b17fb31ea41b9a2b3da0ed9fc4f7d.jpg', '["/uploads/fruit-images/a82b17fb31ea41b9a2b3da0ed9fc4f7d.jpg"]', '["/uploads/fruit-images/7abe309f132d4f78bf2ea27b6c78cda0.jpg"]', '', '斤', '斤', 'in_stock', 0, '2026-06-28 14:17:17', '2026-06-29 15:14:48'),
	(15, '黄柠檬', 9, '柠檬 | 金桔', '/uploads/fruit-images/2e0ef5c047d949f3b8f0e3ee5ef91c7a.jpg', '["/uploads/fruit-images/2e0ef5c047d949f3b8f0e3ee5ef91c7a.jpg"]', '["/uploads/fruit-images/a3d4c72b1e364d39a64e522c6fb5e867.jpg"]', '', '斤', '斤', 'in_stock', 0, '2026-06-28 14:18:43', '2026-06-29 15:17:26'),
	(16, '香水柠檬', 9, '柠檬 | 金桔', '/uploads/fruit-images/178e5752aa6d44679e313301fe7a2e77.jpg', '["/uploads/fruit-images/178e5752aa6d44679e313301fe7a2e77.jpg"]', '["/uploads/fruit-images/481096fd58d944889e4c42118e89e382.jpg"]', '', '斤', '斤', 'in_stock', 0, '2026-06-28 14:19:06', '2026-06-29 17:41:53'),
	(17, '红柚', 10, '芭乐|柚子|百香果', '/uploads/fruit-images/d53ea307c1b649fda21f307f3d873b10.jpg', '["/uploads/fruit-images/d53ea307c1b649fda21f307f3d873b10.jpg"]', '["/uploads/fruit-images/a602704875d24a39aff853cf67adaeac.jpg"]', '', '斤', '斤', 'in_stock', 0, '2026-06-28 14:30:13', '2026-06-29 15:19:19'),
	(18, '姑娘果', 1, '应季水果', '/uploads/fruit-images/8829c123bddf40df85f1a557b5dddb36.jpg', '["/uploads/fruit-images/8829c123bddf40df85f1a557b5dddb36.jpg"]', '["/uploads/fruit-images/dee659247721474489a0091239d5f019.jpg", "/uploads/fruit-images/c5924be939e24f4d8dbf031beb3dd60e.jpg"]', '', '斤', '斤', 'in_stock', 0, '2026-06-28 14:31:23', '2026-06-29 15:01:06'),
	(19, '草莓盆装', 8, '莓果', NULL, '[]', '[]', '', '斤', '斤', 'out_of_stock', 0, '2026-06-28 14:31:53', '2026-06-29 15:09:53'),
	(20, '猕猴桃', 11, '奇异果|猕猴桃', '/uploads/fruit-images/6bfe5aeb87d1478e830b5ac3b938222f.jpg', '["/uploads/fruit-images/6bfe5aeb87d1478e830b5ac3b938222f.jpg"]', '["/uploads/fruit-images/316f697fa91d469d8a2c09ecd95b356a.jpg"]', '', '斤', '斤', 'in_stock', 0, '2026-06-28 14:32:33', '2026-06-29 15:19:52'),
	(21, '青柠檬', 9, '柠檬 | 金桔', '/uploads/fruit-images/a308576cf66242cc826c1bcc1dfbb553.jpg', '["/uploads/fruit-images/a308576cf66242cc826c1bcc1dfbb553.jpg"]', '["/uploads/fruit-images/a9784d38489e43f08a15e70c90711f14.jpg"]', '', '斤', '斤', 'in_stock', 0, '2026-06-28 14:32:56', '2026-06-29 15:17:52'),
	(22, '无花果', 1, '应季水果', NULL, '[]', '[]', '', '斤', '斤', 'in_stock', 0, '2026-06-28 14:33:15', '2026-06-28 14:33:15'),
	(23, '金桔', 9, '柠檬 | 金桔', '/uploads/fruit-images/07786f11795e4717a55f39d4736a31d5.jpg', '["/uploads/fruit-images/07786f11795e4717a55f39d4736a31d5.jpg"]', '["/uploads/fruit-images/04b1c7e9908b40228ea63ecc8f305a10.jpg"]', '', '斤', '斤', 'in_stock', 0, '2026-06-28 14:33:48', '2026-06-29 17:42:10'),
	(24, '沃柑', 5, '柑橘橙', '/uploads/fruit-images/be5823e282a041feb7faecd1241cacbf.jpg', '["/uploads/fruit-images/be5823e282a041feb7faecd1241cacbf.jpg"]', '["/uploads/fruit-images/524ea2613d894c81810e1c4005dd4486.jpg", "/uploads/fruit-images/149ed34b0a9b442f864a325522475a0b.jpg"]', '', '斤', '斤', 'in_stock', 0, '2026-06-28 14:34:14', '2026-06-29 15:13:22'),
	(25, '树莓', 8, '莓果', '/uploads/fruit-images/5aa91c128e854a8d88e2176506fff37c.jpg', '["/uploads/fruit-images/5aa91c128e854a8d88e2176506fff37c.jpg"]', '["/uploads/fruit-images/e20741cddde8492dada2868800f7441f.jpg"]', '', '盒', '盒', 'in_stock', 0, '2026-06-28 14:34:41', '2026-06-29 15:10:45'),
	(26, '网纹瓜', 7, '瓜类', '/uploads/fruit-images/c379a8936c924d4495760c3143241c7e.jpg', '["/uploads/fruit-images/c379a8936c924d4495760c3143241c7e.jpg"]', '["/uploads/fruit-images/32402bb7cc324a8da202b8a5b8fa26af.jpg"]', '', '斤', '斤', 'in_stock', 0, '2026-06-28 14:35:03', '2026-06-29 15:16:27'),
	(27, '丹东草莓', 8, '莓果', NULL, '[]', '[]', '', '盒', '盒', 'out_of_stock', 0, '2026-06-28 14:35:27', '2026-06-29 15:10:38'),
	(28, '龙眼', 1, '应季水果', NULL, '[]', '[]', '', '斤', '斤', 'in_stock', 0, '2026-06-28 14:36:01', '2026-06-28 14:36:01'),
	(29, '黄金柳芽', 12, '柳芽', '/uploads/fruit-images/8b3ea8c1ead4427d85f0372da44e9557.jpg', '["/uploads/fruit-images/8b3ea8c1ead4427d85f0372da44e9557.jpg"]', '["/uploads/fruit-images/2016f6a595c84b3a890ecf068af9677c.jpg"]', '', '盒', '盒', 'in_stock', 0, '2026-06-28 14:36:42', '2026-06-29 15:21:19'),
	(30, '黄桃罐头', 13, '水果制品', '/uploads/fruit-images/4e57b24ae443490b93b0ae8fe4570f82.jpg', '["/uploads/fruit-images/4e57b24ae443490b93b0ae8fe4570f82.jpg"]', '["/uploads/fruit-images/3d9c94caa90044efba6491dd3f166ead.jpg"]', '', '箱', '箱', 'in_stock', 0, '2026-06-28 14:37:50', '2026-06-29 15:20:37'),
	(31, '樱桃', 1, '应季水果', '/uploads/fruit-images/878d214916a74678875e80fc11b038b5.jpg', '["/uploads/fruit-images/878d214916a74678875e80fc11b038b5.jpg"]', '["/uploads/fruit-images/cf9e670a4ab54fadb2c316ad6754b2b3.jpg"]', '', '斤', '斤', 'in_stock', 0, '2026-06-28 14:38:54', '2026-06-29 15:02:50'),
	(32, '双流草莓', 8, '莓果', '/uploads/fruit-images/5bd7a26d91f145e69476107fc61a0de0.jpg', '["/uploads/fruit-images/5bd7a26d91f145e69476107fc61a0de0.jpg"]', '["/uploads/fruit-images/4fd01a26b9f14002abb7b4b151a2793f.jpg", "/uploads/fruit-images/4eed1567bac74078ac8f91015bd42947.jpg"]', '', '盒', '盒', 'in_stock', 0, '2026-06-28 14:39:22', '2026-06-29 15:10:28'),
	(33, '无籽红提', 3, '葡提', '/uploads/fruit-images/7f3bebaeffa84756ae94741afd787a39.jpg', '["/uploads/fruit-images/7f3bebaeffa84756ae94741afd787a39.jpg"]', '["/uploads/fruit-images/2d9defad112e4abf9b8b4e8bdb6a3805.jpg"]', '', '斤', '斤', 'in_stock', 0, '2026-06-28 14:39:45', '2026-06-29 15:02:27'),
	(34, '杨梅', 1, '应季水果', '/uploads/fruit-images/085d49c252a94b639e88a5f8e960f989.jpg', '["/uploads/fruit-images/085d49c252a94b639e88a5f8e960f989.jpg"]', '["/uploads/fruit-images/dcd94433143c4a70abe17c6dad8334dd.jpg", "/uploads/fruit-images/eae10ec30f644d42bb17df307f8a4485.jpg"]', '', '斤', '斤', 'in_stock', 1, '2026-06-28 14:40:15', '2026-06-29 14:58:12'),
	(35, '荔枝', 1, '应季水果', NULL, '[]', '[]', '', '斤', '斤', 'in_stock', 0, '2026-06-28 14:40:28', '2026-06-28 14:40:28'),
	(36, '玉菇甜瓜', 7, '瓜类', '/uploads/fruit-images/6d54f99ddaab44e88627fef9b4ae2493.jpg', '["/uploads/fruit-images/6d54f99ddaab44e88627fef9b4ae2493.jpg"]', '[]', '', '斤', '斤', 'out_of_stock', 0, '2026-06-28 14:45:06', '2026-06-29 17:42:33');
/*!40000 ALTER TABLE `fruits` ENABLE KEYS */;

-- 导出  表 fruit_quote.fruit_categories 结构
DROP TABLE IF EXISTS `fruit_categories`;
CREATE TABLE IF NOT EXISTS `fruit_categories` (
  `id` int(11) NOT NULL AUTO_INCREMENT,
  `name` varchar(60) COLLATE utf8mb4_unicode_ci NOT NULL,
  `icon` varchar(64) COLLATE utf8mb4_unicode_ci DEFAULT NULL,
  `sort_order` int(11) NOT NULL,
  `is_active` tinyint(1) NOT NULL,
  `created_at` datetime NOT NULL DEFAULT CURRENT_TIMESTAMP,
  `updated_at` datetime NOT NULL DEFAULT CURRENT_TIMESTAMP,
  `icon_url` text COLLATE utf8mb4_unicode_ci,
  PRIMARY KEY (`id`),
  UNIQUE KEY `ix_fruit_categories_name` (`name`),
  KEY `ix_fruit_categories_id` (`id`),
  KEY `ix_fruit_categories_sort_order` (`sort_order`),
  KEY `ix_fruit_categories_is_active` (`is_active`)
) ENGINE=InnoDB AUTO_INCREMENT=14 DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- 正在导出表  fruit_quote.fruit_categories 的数据：~13 rows (大约)
/*!40000 ALTER TABLE `fruit_categories` DISABLE KEYS */;
INSERT INTO `fruit_categories` (`id`, `name`, `icon`, `sort_order`, `is_active`, `created_at`, `updated_at`, `icon_url`) VALUES
	(1, '应季水果', NULL, 10, 1, '2026-06-27 14:03:25', '2026-07-03 02:39:36', '/uploads/fruit-images/dc41e1eeefc7439f8046dfa7cccde742.png'),
	(2, '芒果', NULL, 20, 1, '2026-06-27 14:14:13', '2026-07-03 02:44:46', '/uploads/fruit-images/e0a4081d87ea401db335be83f90359ba.png'),
	(3, '葡提', NULL, 30, 1, '2026-06-28 14:10:04', '2026-06-28 14:10:04', NULL),
	(4, '火龙果', NULL, 40, 1, '2026-06-28 14:11:01', '2026-06-28 14:11:01', NULL),
	(5, '柑橘橙', NULL, 50, 1, '2026-06-28 14:12:41', '2026-06-28 14:12:41', NULL),
	(6, '凤梨 | 菠萝', NULL, 60, 1, '2026-06-28 14:13:37', '2026-06-28 14:13:37', NULL),
	(7, '瓜类', NULL, 70, 1, '2026-06-28 14:14:59', '2026-06-28 14:14:59', NULL),
	(8, '莓果', NULL, 80, 1, '2026-06-28 14:16:12', '2026-06-28 14:16:12', NULL),
	(9, '柠檬 | 金桔', NULL, 90, 1, '2026-06-28 14:18:08', '2026-06-28 14:18:08', NULL),
	(10, '芭乐|柚子|百香果', NULL, 100, 1, '2026-06-28 14:29:35', '2026-06-28 14:29:35', NULL),
	(11, '奇异果|猕猴桃', NULL, 110, 1, '2026-06-28 14:32:13', '2026-06-28 14:32:13', NULL),
	(12, '柳芽', NULL, 129, 1, '2026-06-28 14:36:20', '2026-06-28 14:37:18', NULL),
	(13, '水果制品', NULL, 120, 1, '2026-06-28 14:36:59', '2026-06-28 14:37:23', NULL);
/*!40000 ALTER TABLE `fruit_categories` ENABLE KEYS */;

-- 导出  表 fruit_quote.orders 结构
DROP TABLE IF EXISTS `orders`;
CREATE TABLE IF NOT EXISTS `orders` (
  `id` int(11) NOT NULL AUTO_INCREMENT,
  `order_no` varchar(32) COLLATE utf8mb4_unicode_ci NOT NULL,
  `customer_id` int(11) NOT NULL,
  `status` varchar(32) COLLATE utf8mb4_unicode_ci NOT NULL,
  `estimated_total` decimal(12,2) NOT NULL,
  `receiver_name` varchar(60) COLLATE utf8mb4_unicode_ci NOT NULL,
  `receiver_phone` varchar(32) COLLATE utf8mb4_unicode_ci NOT NULL,
  `province` varchar(60) COLLATE utf8mb4_unicode_ci NOT NULL,
  `city` varchar(60) COLLATE utf8mb4_unicode_ci NOT NULL,
  `district` varchar(60) COLLATE utf8mb4_unicode_ci NOT NULL,
  `detail_address` varchar(255) COLLATE utf8mb4_unicode_ci NOT NULL,
  `delivery_note` text COLLATE utf8mb4_unicode_ci,
  `email_notify_status` varchar(32) COLLATE utf8mb4_unicode_ci NOT NULL,
  `created_at` datetime NOT NULL DEFAULT CURRENT_TIMESTAMP,
  `updated_at` datetime NOT NULL DEFAULT CURRENT_TIMESTAMP,
  `coupon_id` int(11) DEFAULT NULL,
  `discount_amount` decimal(12,2) NOT NULL DEFAULT '0.00',
  `payable_total` decimal(12,2) NOT NULL DEFAULT '0.00',
  `delivery_fee` decimal(12,2) NOT NULL DEFAULT '0.00',
  `paid_amount` decimal(12,2) NOT NULL DEFAULT '0.00',
  PRIMARY KEY (`id`),
  UNIQUE KEY `ix_orders_order_no` (`order_no`),
  KEY `ix_orders_status` (`status`),
  KEY `ix_orders_id` (`id`),
  KEY `ix_orders_customer_id` (`customer_id`),
  KEY `ix_orders_coupon_id` (`coupon_id`),
  CONSTRAINT `orders_ibfk_1` FOREIGN KEY (`customer_id`) REFERENCES `customers` (`id`)
) ENGINE=InnoDB AUTO_INCREMENT=3 DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- 正在导出表  fruit_quote.orders 的数据：~2 rows (大约)
/*!40000 ALTER TABLE `orders` DISABLE KEYS */;
INSERT INTO `orders` (`id`, `order_no`, `customer_id`, `status`, `estimated_total`, `receiver_name`, `receiver_phone`, `province`, `city`, `district`, `detail_address`, `delivery_note`, `email_notify_status`, `created_at`, `updated_at`, `coupon_id`, `discount_amount`, `payable_total`, `delivery_fee`, `paid_amount`) VALUES
	(1, 'F20260630152306389', 8, 'confirmed', 10.00, 'x', '15070511241', '上海', '上海', '嘉定', '嘉松中路99号', '', 'failed', '2026-06-30 15:23:06', '2026-06-30 15:24:22', NULL, 0.00, 10.00, 0.00, 10.00),
	(2, 'F20260710150340507', 2, 'pending', 10.00, '谢', '15770511044', '上海', '上海', '松江区', '文亭苑425弄', '', 'failed', '2026-07-10 15:03:40', '2026-07-10 15:03:40', NULL, 0.00, 10.00, 0.00, 10.00);
/*!40000 ALTER TABLE `orders` ENABLE KEYS */;

-- 导出  表 fruit_quote.orders_bak20260916 结构
DROP TABLE IF EXISTS `orders_bak20260916`;
CREATE TABLE IF NOT EXISTS `orders_bak20260916` (
  `id` int(11) NOT NULL AUTO_INCREMENT,
  `order_no` varchar(32) COLLATE utf8mb4_unicode_ci NOT NULL,
  `customer_id` int(11) NOT NULL,
  `status` varchar(32) COLLATE utf8mb4_unicode_ci NOT NULL,
  `estimated_total` decimal(12,2) NOT NULL,
  `receiver_name` varchar(60) COLLATE utf8mb4_unicode_ci NOT NULL,
  `receiver_phone` varchar(32) COLLATE utf8mb4_unicode_ci NOT NULL,
  `province` varchar(60) COLLATE utf8mb4_unicode_ci NOT NULL,
  `city` varchar(60) COLLATE utf8mb4_unicode_ci NOT NULL,
  `district` varchar(60) COLLATE utf8mb4_unicode_ci NOT NULL,
  `detail_address` varchar(255) COLLATE utf8mb4_unicode_ci NOT NULL,
  `delivery_note` text COLLATE utf8mb4_unicode_ci,
  `email_notify_status` varchar(32) COLLATE utf8mb4_unicode_ci NOT NULL,
  `created_at` datetime NOT NULL DEFAULT CURRENT_TIMESTAMP,
  `updated_at` datetime NOT NULL DEFAULT CURRENT_TIMESTAMP,
  PRIMARY KEY (`id`),
  UNIQUE KEY `ix_orders_order_no` (`order_no`),
  KEY `ix_orders_status` (`status`),
  KEY `ix_orders_id` (`id`),
  KEY `ix_orders_customer_id` (`customer_id`)
) ENGINE=InnoDB AUTO_INCREMENT=3 DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- 正在导出表  fruit_quote.orders_bak20260916 的数据：~2 rows (大约)
/*!40000 ALTER TABLE `orders_bak20260916` DISABLE KEYS */;
INSERT INTO `orders_bak20260916` (`id`, `order_no`, `customer_id`, `status`, `estimated_total`, `receiver_name`, `receiver_phone`, `province`, `city`, `district`, `detail_address`, `delivery_note`, `email_notify_status`, `created_at`, `updated_at`) VALUES
	(1, 'F20260630152306389', 8, 'confirmed', 10.00, 'x', '15070511241', '上海', '上海', '嘉定', '嘉松中路99号', '', 'failed', '2026-06-30 15:23:06', '2026-06-30 15:24:22'),
	(2, 'F20260710150340507', 2, 'pending', 10.00, '谢', '15770511044', '上海', '上海', '松江区', '文亭苑425弄', '', 'failed', '2026-07-10 15:03:40', '2026-07-10 15:03:40');
/*!40000 ALTER TABLE `orders_bak20260916` ENABLE KEYS */;

-- 导出  表 fruit_quote.order_items 结构
DROP TABLE IF EXISTS `order_items`;
CREATE TABLE IF NOT EXISTS `order_items` (
  `id` int(11) NOT NULL AUTO_INCREMENT,
  `order_id` int(11) NOT NULL,
  `fruit_id` int(11) NOT NULL,
  `fruit_name` varchar(80) COLLATE utf8mb4_unicode_ci NOT NULL,
  `spec` varchar(120) COLLATE utf8mb4_unicode_ci NOT NULL,
  `unit` varchar(20) COLLATE utf8mb4_unicode_ci NOT NULL,
  `price` decimal(10,2) NOT NULL,
  `quantity` decimal(10,2) NOT NULL,
  `subtotal` decimal(12,2) NOT NULL,
  PRIMARY KEY (`id`),
  KEY `ix_order_items_fruit_id` (`fruit_id`),
  KEY `ix_order_items_id` (`id`),
  KEY `ix_order_items_order_id` (`order_id`),
  CONSTRAINT `order_items_ibfk_1` FOREIGN KEY (`order_id`) REFERENCES `orders` (`id`),
  CONSTRAINT `order_items_ibfk_2` FOREIGN KEY (`fruit_id`) REFERENCES `fruits` (`id`)
) ENGINE=InnoDB AUTO_INCREMENT=3 DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- 正在导出表  fruit_quote.order_items 的数据：~2 rows (大约)
/*!40000 ALTER TABLE `order_items` DISABLE KEYS */;
INSERT INTO `order_items` (`id`, `order_id`, `fruit_id`, `fruit_name`, `spec`, `unit`, `price`, `quantity`, `subtotal`) VALUES
	(1, 1, 34, '杨梅', '斤', '斤', 10.00, 1.00, 10.00),
	(2, 2, 34, '杨梅', '斤', '斤', 10.00, 1.00, 10.00);
/*!40000 ALTER TABLE `order_items` ENABLE KEYS */;

-- 导出  表 fruit_quote.order_payments 结构
DROP TABLE IF EXISTS `order_payments`;
CREATE TABLE IF NOT EXISTS `order_payments` (
  `id` int(11) NOT NULL AUTO_INCREMENT,
  `order_id` int(11) NOT NULL,
  `out_trade_no` varchar(64) COLLATE utf8mb4_unicode_ci NOT NULL,
  `kind` varchar(16) COLLATE utf8mb4_unicode_ci NOT NULL DEFAULT 'initial',
  `amount` decimal(12,2) NOT NULL DEFAULT '0.00',
  `status` varchar(16) COLLATE utf8mb4_unicode_ci NOT NULL DEFAULT 'pending',
  `prepay_id` varchar(128) COLLATE utf8mb4_unicode_ci DEFAULT NULL,
  `transaction_id` varchar(64) COLLATE utf8mb4_unicode_ci DEFAULT NULL,
  `refund_id` varchar(64) COLLATE utf8mb4_unicode_ci DEFAULT NULL,
  `pending_payload` text COLLATE utf8mb4_unicode_ci,
  `created_at` datetime DEFAULT CURRENT_TIMESTAMP,
  `updated_at` datetime DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
  `paid_at` datetime DEFAULT NULL,
  `refunded_at` datetime DEFAULT NULL,
  PRIMARY KEY (`id`),
  UNIQUE KEY `uq_order_payments_out_trade_no` (`out_trade_no`),
  KEY `ix_order_payments_order_id` (`order_id`),
  KEY `ix_order_payments_status` (`status`),
  KEY `ix_order_payments_transaction_id` (`transaction_id`)
) ENGINE=MyISAM AUTO_INCREMENT=3 DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- 正在导出表  fruit_quote.order_payments 的数据：0 rows
/*!40000 ALTER TABLE `order_payments` DISABLE KEYS */;
/*!40000 ALTER TABLE `order_payments` ENABLE KEYS */;

-- 导出  表 fruit_quote.price_quotes 结构
DROP TABLE IF EXISTS `price_quotes`;
CREATE TABLE IF NOT EXISTS `price_quotes` (
  `id` int(11) NOT NULL AUTO_INCREMENT,
  `fruit_id` int(11) NOT NULL,
  `normal_price` decimal(10,2) NOT NULL,
  `verified_price` decimal(10,2) NOT NULL,
  `grade` varchar(60) COLLATE utf8mb4_unicode_ci NOT NULL,
  `min_order_quantity` decimal(10,2) NOT NULL,
  `note` text COLLATE utf8mb4_unicode_ci,
  `created_at` datetime NOT NULL DEFAULT CURRENT_TIMESTAMP,
  `updated_at` datetime NOT NULL DEFAULT CURRENT_TIMESTAMP,
  PRIMARY KEY (`id`),
  UNIQUE KEY `ix_price_quotes_fruit_id` (`fruit_id`),
  KEY `ix_price_quotes_id` (`id`),
  CONSTRAINT `price_quotes_ibfk_1` FOREIGN KEY (`fruit_id`) REFERENCES `fruits` (`id`)
) ENGINE=InnoDB AUTO_INCREMENT=37 DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- 正在导出表  fruit_quote.price_quotes 的数据：~36 rows (大约)
/*!40000 ALTER TABLE `price_quotes` DISABLE KEYS */;
INSERT INTO `price_quotes` (`id`, `fruit_id`, `normal_price`, `verified_price`, `grade`, `min_order_quantity`, `note`, `created_at`, `updated_at`) VALUES
	(1, 1, 2.20, 2.00, '一级', 1.00, '', '2026-06-27 14:08:07', '2026-06-27 14:08:07'),
	(2, 2, 18.00, 16.00, '一级', 1.00, '', '2026-06-27 14:12:33', '2026-06-27 14:12:33'),
	(3, 3, 5.00, 4.80, '一级', 1.00, '', '2026-06-27 14:14:56', '2026-06-27 14:14:56'),
	(4, 4, 8.00, 7.00, '一级', 1.00, '', '2026-06-27 14:19:59', '2026-06-27 14:19:59'),
	(5, 5, 13.00, 12.00, '一级', 1.00, '', '2026-06-28 14:10:30', '2026-06-28 14:10:30'),
	(6, 6, 165.00, 160.00, '一级', 1.00, '', '2026-06-28 14:11:30', '2026-06-28 14:11:30'),
	(7, 7, 6.00, 5.80, '一级', 1.00, '', '2026-06-28 14:11:50', '2026-06-28 14:11:50'),
	(8, 8, 4.50, 4.00, '一级', 1.00, '', '2026-06-28 14:13:05', '2026-06-28 14:13:05'),
	(9, 9, 4.50, 4.00, '一级', 1.00, '', '2026-06-28 14:13:56', '2026-06-28 14:13:56'),
	(10, 10, 7.50, 7.00, '一级', 1.00, '', '2026-06-28 14:14:27', '2026-06-28 14:14:27'),
	(11, 11, 4.50, 4.00, '一级', 1.00, '', '2026-06-28 14:15:15', '2026-06-28 14:15:15'),
	(12, 12, 16.00, 15.00, '一级', 1.00, '', '2026-06-28 14:16:35', '2026-06-28 14:16:35'),
	(13, 13, 16.00, 15.00, '一级', 1.00, '', '2026-06-28 14:16:57', '2026-06-28 14:16:57'),
	(14, 14, 4.50, 4.00, '一级', 1.00, '', '2026-06-28 14:17:17', '2026-06-28 14:17:17'),
	(15, 15, 9.00, 8.00, '一级', 1.00, '', '2026-06-28 14:18:43', '2026-06-28 14:18:43'),
	(16, 16, 6.50, 6.00, '一级', 1.00, '', '2026-06-28 14:19:06', '2026-06-28 14:19:06'),
	(17, 17, 14.00, 13.00, '一级', 1.00, '', '2026-06-28 14:30:13', '2026-06-28 14:30:13'),
	(18, 18, 28.00, 25.00, '一级', 1.00, '', '2026-06-28 14:31:23', '2026-06-28 14:31:23'),
	(19, 19, 6.50, 6.00, '一级', 1.00, '', '2026-06-28 14:31:53', '2026-06-28 14:31:53'),
	(20, 20, 4.50, 4.00, '一级', 1.00, '', '2026-06-28 14:32:33', '2026-06-28 14:32:33'),
	(21, 21, 6.50, 6.00, '一级', 1.00, '', '2026-06-28 14:32:56', '2026-06-28 14:32:56'),
	(22, 22, 22.00, 20.00, '一级', 1.00, '', '2026-06-28 14:33:15', '2026-06-28 14:33:15'),
	(23, 23, 6.50, 6.00, '一级', 1.00, '', '2026-06-28 14:33:48', '2026-06-28 14:33:48'),
	(24, 24, 4.50, 4.00, '一级', 1.00, '', '2026-06-28 14:34:14', '2026-06-28 14:34:14'),
	(25, 25, 26.00, 25.00, '一级', 1.00, '', '2026-06-28 14:34:41', '2026-06-28 14:34:41'),
	(26, 26, 6.50, 6.00, '一级', 1.00, '', '2026-06-28 14:35:03', '2026-06-28 14:35:03'),
	(27, 27, 11.00, 10.00, '一级', 1.00, '', '2026-06-28 14:35:27', '2026-06-28 14:35:27'),
	(28, 28, 16.00, 15.00, '一级', 1.00, '', '2026-06-28 14:36:01', '2026-06-28 14:36:01'),
	(29, 29, 4.00, 3.50, '一级', 1.00, '', '2026-06-28 14:36:42', '2026-06-28 14:36:42'),
	(30, 30, 145.00, 140.00, '一级', 1.00, '', '2026-06-28 14:37:50', '2026-06-28 14:37:50'),
	(31, 31, 30.00, 28.00, '一级', 1.00, '', '2026-06-28 14:38:54', '2026-06-28 14:38:54'),
	(32, 32, 9.00, 8.00, '一级', 1.00, '', '2026-06-28 14:39:22', '2026-06-28 14:39:22'),
	(33, 33, 22.00, 20.00, '一级', 1.00, '', '2026-06-28 14:39:45', '2026-06-28 14:39:45'),
	(34, 34, 11.00, 10.00, '一级', 1.00, '', '2026-06-28 14:40:15', '2026-06-28 14:40:15'),
	(35, 35, 18.00, 16.00, '一级', 1.00, '', '2026-06-28 14:40:28', '2026-06-28 14:40:28'),
	(36, 36, 4.50, 4.00, '一级', 1.00, '', '2026-06-28 14:45:06', '2026-06-28 14:45:06');
/*!40000 ALTER TABLE `price_quotes` ENABLE KEYS */;

-- 导出  表 fruit_quote.system_settings 结构
DROP TABLE IF EXISTS `system_settings`;
CREATE TABLE IF NOT EXISTS `system_settings` (
  `id` int(11) NOT NULL AUTO_INCREMENT,
  `key` varchar(80) COLLATE utf8mb4_unicode_ci NOT NULL,
  `value` text COLLATE utf8mb4_unicode_ci NOT NULL,
  `created_at` datetime NOT NULL DEFAULT CURRENT_TIMESTAMP,
  `updated_at` datetime NOT NULL DEFAULT CURRENT_TIMESTAMP,
  PRIMARY KEY (`id`),
  UNIQUE KEY `ix_system_settings_key` (`key`),
  KEY `ix_system_settings_id` (`id`)
) ENGINE=InnoDB AUTO_INCREMENT=6 DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- 正在导出表  fruit_quote.system_settings 的数据：~5 rows (大约)
/*!40000 ALTER TABLE `system_settings` DISABLE KEYS */;
INSERT INTO `system_settings` (`id`, `key`, `value`, `created_at`, `updated_at`) VALUES
	(1, 'supplier_phone', '13800000000', '2026-06-27 13:51:24', '2026-06-27 13:51:24'),
	(2, 'supplier_wechat', 'fruit-supplier', '2026-06-27 13:51:24', '2026-06-27 13:51:24'),
	(3, 'notice', '价格随行情波动，提交预订后以电话确认为准。', '2026-06-27 13:51:24', '2026-06-27 13:51:24'),
	(4, 'delivery_free_threshold', '120', '2026-09-16 17:12:31', '2026-09-16 17:12:31'),
	(5, 'delivery_fee', '10', '2026-09-16 17:12:31', '2026-09-16 17:12:31');
/*!40000 ALTER TABLE `system_settings` ENABLE KEYS */;

/*!40101 SET SQL_MODE=IFNULL(@OLD_SQL_MODE, '') */;
/*!40014 SET FOREIGN_KEY_CHECKS=IF(@OLD_FOREIGN_KEY_CHECKS IS NULL, 1, @OLD_FOREIGN_KEY_CHECKS) */;
/*!40101 SET CHARACTER_SET_CLIENT=@OLD_CHARACTER_SET_CLIENT */;
