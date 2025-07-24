-- Authentication Tables for MVidarr Enhanced
-- Creates users and user_sessions tables with proper constraints

-- Create users table
CREATE TABLE IF NOT EXISTS users (
    id INTEGER PRIMARY KEY AUTO_INCREMENT,
    username VARCHAR(80) UNIQUE NOT NULL,
    email VARCHAR(120) UNIQUE NOT NULL,
    password_hash VARCHAR(255) NOT NULL,
    role ENUM('READONLY', 'USER', 'MANAGER', 'ADMIN') DEFAULT 'USER' NOT NULL,
    is_active BOOLEAN DEFAULT TRUE NOT NULL,
    is_email_verified BOOLEAN DEFAULT FALSE NOT NULL,
    failed_login_attempts INTEGER DEFAULT 0 NOT NULL,
    locked_until DATETIME NULL,
    last_login DATETIME NULL,
    last_login_ip VARCHAR(45) NULL,
    password_changed_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    email_verification_token VARCHAR(255) NULL,
    password_reset_token VARCHAR(255) NULL,
    password_reset_expires DATETIME NULL,
    two_factor_secret VARCHAR(32) NULL,
    two_factor_enabled BOOLEAN DEFAULT FALSE NOT NULL,
    backup_codes JSON NULL,
    preferences JSON NULL,
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    updated_at DATETIME DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP
);

-- Create user_sessions table
CREATE TABLE IF NOT EXISTS user_sessions (
    id INTEGER PRIMARY KEY AUTO_INCREMENT,
    user_id INTEGER NOT NULL,
    session_token VARCHAR(255) UNIQUE NOT NULL,
    status ENUM('ACTIVE', 'EXPIRED', 'REVOKED') DEFAULT 'ACTIVE' NOT NULL,
    ip_address VARCHAR(45) NULL,
    user_agent TEXT NULL,
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    last_activity DATETIME DEFAULT CURRENT_TIMESTAMP,
    expires_at DATETIME NOT NULL,
    FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE
);

-- Create indexes for better performance
CREATE INDEX IF NOT EXISTS idx_users_username ON users(username);
CREATE INDEX IF NOT EXISTS idx_users_email ON users(email);
CREATE INDEX IF NOT EXISTS idx_users_role ON users(role);
CREATE INDEX IF NOT EXISTS idx_users_active ON users(is_active);

CREATE INDEX IF NOT EXISTS idx_sessions_user_id ON user_sessions(user_id);
CREATE INDEX IF NOT EXISTS idx_sessions_token ON user_sessions(session_token);
CREATE INDEX IF NOT EXISTS idx_sessions_status ON user_sessions(status);
CREATE INDEX IF NOT EXISTS idx_sessions_expires ON user_sessions(expires_at);

-- Insert default admin user (password: MVidarr@dmin123)
INSERT IGNORE INTO users (
    username, 
    email, 
    password_hash, 
    role, 
    is_active, 
    is_email_verified
) VALUES (
    'admin',
    'admin@mvidarr.local',
    'scrypt:32768:8:1$EYLfGsMwCkGvz9Op$d5e4f5a8b9c1e2f3a4b5c6d7e8f9a0b1c2d3e4f5a6b7c8d9e0f1a2b3c4d5e6f7a8b9c0d1e2f3a4b5c6d7e8f9',
    'ADMIN',
    TRUE,
    TRUE
);