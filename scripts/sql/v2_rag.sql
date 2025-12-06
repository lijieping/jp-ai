-- 业务空间表
CREATE TABLE IF NOT EXISTS ai_agent.rag_kb_space (
    id                  BIGINT AUTO_INCREMENT PRIMARY KEY,
    name                VARCHAR(128) NOT NULL COMMENT '显示名',
    description         TEXT COMMENT '描述',
    vector_db_collection VARCHAR(128) NOT NULL COMMENT '对应的集合/表/索引名',
    status              TINYINT DEFAULT 1 COMMENT '1正常 0假删除',
    created_at          DATETIME DEFAULT CURRENT_TIMESTAMP,
    updated_at          DATETIME DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP
);

-- 知识文件主表
CREATE TABLE  IF NOT EXISTS ai_agent.kb_file (
    id          BIGINT AUTO_INCREMENT PRIMARY KEY,
    space_id    BIGINT NOT NULL COMMENT '空间ID',               -- 关联 biz_space
    title       VARCHAR(255) NOT NULL COMMENT '文档标题',
    file_name   VARCHAR(255) NOT NULL COMMENT '原始文件名',
    description   TEXT  DEFAULT NULL  COMMENT '描述',
    file_type   VARCHAR(64)  NOT NULL COMMENT '扩展名 pdf/md/txt...',
    file_size   BIGINT NOT NULL COMMENT '字节数',
    file_url    VARCHAR(500) COMMENT '对象存储地址',
    file_hash   CHAR(64) NOT NULL COMMENT 'SHA256 去重/秒传',
    status      TINYINT NOT NULL DEFAULT 1 COMMENT '0-失效 1-索引中 2-索引完成 3-索引失败',
    user_id     BIGINT NOT NULL COMMENT '上传人用户ID',
    created_at  DATETIME DEFAULT CURRENT_TIMESTAMP,
    updated_at  DATETIME DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    INDEX idx_space (space_id),
    INDEX idx_hash  (file_hash),
    INDEX idx_status (status)
);

-- 文件rag检索状态
CREATE TABLE IF NOT EXISTS ai_agent.rag_pipeline_record (
    id            BIGINT UNSIGNED NOT NULL AUTO_INCREMENT,
    file_url      VARCHAR(500)     COMMENT '对象存储地址',
    file_version  INT UNSIGNED    NOT NULL DEFAULT 1,
    status        TINYINT UNSIGNED NOT NULL COMMENT '0=未执行 1=执行中 2=执行成功 3执行失败',
    msg           TEXT            NULL,
    created_at    TIMESTAMP       NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at    TIMESTAMP       NOT NULL DEFAULT CURRENT_TIMESTAMP
                                     ON UPDATE CURRENT_TIMESTAMP,
    PRIMARY KEY (id),
    UNIQUE KEY uk_file_version (file_url, file_version, updated_at),
    KEY idx_status_updated (status, updated_at)
);