## Context
项目当前通过环境变量 `MYSQL_URL` 连接外部 MySQL 服务。需要将 MySQL 8.0 纳入 Docker Compose 管理，使其成为项目的基础设施服务之一。

## Architecture
### 当前架构组件
- **backend**: Python FastAPI 后端服务，通过 `MYSQL_URL` 环境变量连接外部 MySQL
- **web**: Vue/TypeScript 前端服务
- **nacos**: 服务注册与发现、配置管理中间件
- **MySQL**: 当前为外部服务，通过环境变量配置连接

### 新增组件
- **MySQL 8.0**: 数据库服务（从外部服务转为基础设施服务）
  - 提供数据持久化存储
  - 支持开发和生产环境的独立实例
  - 通过 Docker 服务名进行服务间通信

## Goals / Non-Goals
- Goals:
  - 在 Docker Compose 中集成 MySQL 8.0 服务
  - 支持开发和生产环境的独立数据库实例
  - 确保数据持久化
  - 简化部署流程（无需外部 MySQL 服务）
- Non-Goals:
  - 不在此阶段进行数据库迁移（保持现有数据库结构）
  - 不配置 MySQL 集群模式（单机模式即可）
  - 不修改数据库连接逻辑（仅更新连接地址）

## Decisions
- Decision: 使用官方 MySQL 8.0 Docker 镜像 `mysql:8.0`
- Alternatives considered:
  - MySQL 8.1/8.2：8.0 是稳定版本，兼容性更好
  - MariaDB：保持与现有 MySQL 兼容性

- Decision: 使用环境变量配置 MySQL root 密码和默认数据库
- Alternatives considered:
  - 配置文件：环境变量更灵活，适合 Docker Compose

- Decision: 端口映射 3306（标准 MySQL 端口）
- Alternatives considered:
  - 不映射端口：需要映射以便外部工具访问（如数据库管理工具）

- Decision: 使用 Docker 服务名 `mysql` 作为连接地址
- Alternatives considered:
  - localhost：Docker 网络中使用服务名更可靠

## Risks / Trade-offs
- 风险：数据迁移 → 缓解：保持现有数据库结构，仅更新连接地址
- 风险：端口冲突 → 缓解：如果主机已有 MySQL，可修改端口映射
- 权衡：外部服务 vs 容器化 → 选择容器化，简化部署但增加资源占用

## Migration Plan
1. 添加 MySQL 服务到 docker-compose 文件
2. 更新 backend 服务的 MYSQL_URL 环境变量
3. 启动服务验证连接
4. 确认数据持久化正常工作
5. 更新项目文档

## Open Questions
- 是否需要配置 MySQL 字符集和时区？（使用默认配置）
- 是否需要配置 MySQL 性能参数？（使用默认配置）

