# Change: 添加 MySQL 8.0 服务

## Why
项目当前通过环境变量连接外部 MySQL 服务，需要将 MySQL 8.0 纳入 Docker Compose 统一管理，以简化部署流程、确保数据持久化，并支持开发和生产环境的独立数据库实例。

## What Changes
- 在 docker-compose.yml 和 docker-compose.dev.yml 中添加 MySQL 8.0 服务配置
- 配置 MySQL 的数据持久化存储
- 更新 backend 服务的 MYSQL_URL 环境变量，从外部地址改为 Docker 服务名
- 配置 MySQL 的默认数据库、用户名和密码
- 确保 MySQL 服务在开发和生产环境中的可用性

## Impact
- 受影响的基础设施：Docker Compose 配置
- 受影响的文件：
  - `docker-compose.yml`
  - `docker-compose.dev.yml`
  - `openspec/project.md`（需要将 MySQL 8.0 从"外部服务"移动到"基础设施服务"）
- 新增服务：MySQL 8.0（包含数据持久化）
- 配置变更：backend 服务的 MYSQL_URL 环境变量需要更新

