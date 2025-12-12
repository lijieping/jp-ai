CREATE DATABASE IF NOT EXISTS ai_agent
CHARACTER SET utf8mb4
COLLATE utf8mb4_0900_ai_ci;

-- 用户表
CREATE TABLE IF NOT EXISTS ai_agent.user (
    user_id    BIGINT AUTO_INCREMENT PRIMARY KEY,
    username   VARCHAR(50) NOT NULL UNIQUE,
    password   VARCHAR(255) NOT NULL,
    role       ENUM('admin','user','guest') NOT NULL DEFAULT 'user',
    status     TINYINT DEFAULT 1 COMMENT '1正常 0假删除',
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    updated_at DATETIME DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP
) ENGINE = InnoDB;

-- 插入用户， 明文密码都是123456
INSERT INTO ai_agent.user (user_id, username, password, role, status)
VALUES (250, 'admin', '$2b$12$gaSAzzSYc6BQ9d.ohfgW.ezWYIsoHf0.EEGGxze5/Q34Ap/6ODi5a', 'user', 1);
VALUES (666, 'guest', '$2b$12$e9SCIUwzd0pQK47agB3pTejurarPUXNkBJmh.OV87lpuhouk4Y2sW', 'guest', 1);

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
    msg_id     CHAR(100) PRIMARY KEY,
    conv_id    CHAR(26) NOT NULL,
    role       ENUM('user','assistant') NOT NULL,
    content    MEDIUMTEXT NOT NULL,
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    INDEX idx_conv_turn (conv_id)
) ENGINE = InnoDB;