-- MVidarr Database Initialization Script
CREATE DATABASE IF NOT EXISTS mvidarr CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;
USE mvidarr;
CREATE TABLE IF NOT EXISTS database_status (
    id INT AUTO_INCREMENT PRIMARY KEY,
    status VARCHAR(50) NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);
INSERT INTO database_status (status) VALUES ('initialized') 
ON DUPLICATE KEY UPDATE status = 'initialized', created_at = CURRENT_TIMESTAMP;
EOF < /dev/null
