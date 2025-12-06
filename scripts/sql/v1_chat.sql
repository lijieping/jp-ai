CREATE DATABASE IF NOT EXISTS ai_agent
CHARACTER SET utf8mb4
COLLATE utf8mb4_unicode_ci;

-- 用户表
CREATE TABLE IF NOT EXISTS ai_agent.user (
    user_id    BIGINT AUTO_INCREMENT PRIMARY KEY,
    username   VARCHAR(50) NOT NULL UNIQUE,
    password   VARCHAR(255) NOT NULL,
    role       ENUM('admin','user') NOT NULL DEFAULT 'user',
    status     TINYINT DEFAULT 1 COMMENT '1正常 0假删除',
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    updated_at DATETIME DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP
) ENGINE = InnoDB;

-- 密码 = bcrypt.hashpw("beta123".encode(), bcrypt.gensalt()) 结果截断
INSERT INTO ai_agent.user (user_id, username, password, role, status)
VALUES (250, 'inner_beta', '$2b$12$wWBJGvJ5b6K/9uFZyKpPu.PpZzxxNyK6YfGvJ5b6K/9uFZyKpPu', 'user', 1);

-- 会话表
CREATE TABLE IF NOT EXISTS ai_agent.conversation (
    conv_id    CHAR(26) PRIMARY KEY,
    user_id    BIGINT NOT NULL,
    title      VARCHAR(255) NOT NULL DEFAULT '' COMMENT '会话标题',
    status     TINYINT DEFAULT 1 COMMENT '1正常 0假删除',
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    updated_at DATETIME DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    meta       JSON DEFAULT ('{}')
) ENGINE = InnoDB;

-- 消息表
CREATE TABLE IF NOT EXISTS ai_agent.message (
    msg_id     CHAR(26) PRIMARY KEY,
    conv_id    CHAR(26) NOT NULL,
    role       ENUM('user','assistant') NOT NULL,
    content    MEDIUMTEXT NOT NULL,
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    INDEX idx_conv_turn (conv_id)
) ENGINE = InnoDB;