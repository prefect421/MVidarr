-- MVidarr Enhanced Database Initialization
-- This script sets up the MariaDB database with proper configuration

-- Set character set and collation for proper UTF-8 support
SET NAMES utf8mb4;

-- Create database if it doesn't exist
CREATE DATABASE IF NOT EXISTS mvidarr_enhanced
  CHARACTER SET utf8mb4
  COLLATE utf8mb4_unicode_ci;

-- Use the database
USE mvidarr_enhanced;

-- Grant permissions to the mvidarr user
GRANT ALL PRIVILEGES ON mvidarr_enhanced.* TO 'mvidarr'@'%';
FLUSH PRIVILEGES;

-- Optimize database settings for MVidarr Enhanced
-- These settings are tuned for music video management workloads

-- Set timezone to UTC for consistency
SET time_zone = '+00:00';

-- Performance optimization
SET SESSION sql_mode = 'STRICT_TRANS_TABLES,NO_ZERO_DATE,NO_ZERO_IN_DATE,ERROR_FOR_DIVISION_BY_ZERO';

-- Success message
SELECT 'MVidarr Enhanced database initialized successfully' AS message;