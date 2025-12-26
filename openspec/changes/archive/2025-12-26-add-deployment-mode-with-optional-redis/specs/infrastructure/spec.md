## ADDED Requirements

### Requirement: 部署模式配置
系统 SHALL 支持通过 `MODE` 环境变量指定部署模式，支持 `std`（标准模式）和 `lite`（轻量模式）两种模式。

#### Scenario: 标准模式配置
- **WHEN** `MODE` 环境变量设置为 `std`
- **THEN** 系统应启动所有标准组件，包括 Redis 服务

#### Scenario: 轻量模式配置
- **WHEN** `MODE` 环境变量设置为 `lite` 或未设置
- **THEN** 系统应仅启动核心组件，不启动 Redis 服务

#### Scenario: 模式环境变量传递
- **WHEN** Docker Compose 中设置 `MODE` 环境变量
- **THEN** Backend 服务应能够读取相同的 `MODE` 值

### Requirement: Redis 可选服务部署
系统 SHALL 在 Docker Compose 环境中提供 Redis 8.4.0 服务，但仅在标准模式下启动。

#### Scenario: 标准模式下 Redis 启动
- **WHEN** `MODE=std` 且 Docker Compose 启动时
- **THEN** Redis 8.4.0 服务应成功启动并可用

#### Scenario: 轻量模式下 Redis 不启动
- **WHEN** `MODE=lite` 或未设置且 Docker Compose 启动时
- **THEN** Redis 8.4.0 服务不应启动

#### Scenario: Backend 连接 Redis（标准模式）
- **WHEN** Backend 服务在标准模式下启动且 Redis 服务可用
- **THEN** Backend 应能够成功连接到 Redis

#### Scenario: Backend 无 Redis 运行（轻量模式）
- **WHEN** Backend 服务在轻量模式下启动
- **THEN** Backend 应能够在无 Redis 的情况下正常运行

#### Scenario: Redis 数据持久化
- **WHEN** Redis 服务重启（标准模式下）
- **THEN** Redis 数据应被保留（通过卷挂载）

#### Scenario: 开发和生产环境支持
- **WHEN** 在开发或生产环境中使用 Docker Compose
- **THEN** Redis 服务应在两个环境中都支持模式控制

#### Scenario: Redis 版本和镜像
- **WHEN** Redis 服务在标准模式下启动
- **THEN** 应使用 Redis 8.4.0 版本（镜像：`redis:8.4.0`）

### Requirement: 项目文档更新
系统 SHALL 在 `openspec/project.md` 中记录 Redis 8.4.0 服务的配置信息，包括版本、镜像、端口、数据持久化和部署模式要求。

#### Scenario: 基础设施服务文档更新
- **WHEN** Redis 服务集成完成后
- **THEN** `openspec/project.md` 的"基础设施服务"部分应包含 Redis 8.4.0 的详细说明（版本、镜像、端口、数据持久化、用途等）

#### Scenario: 外部依赖文档更新
- **WHEN** Redis 服务集成完成后
- **THEN** `openspec/project.md` 的"External Dependencies"部分应明确 Redis 版本为 8.4.0，并说明仅在标准模式下启动

## MODIFIED Requirements

### Requirement: MySQL 8.0 服务部署
系统 SHALL 在 Docker Compose 环境中提供 MySQL 8.0 数据库服务，用于应用数据存储。MySQL 服务在所有部署模式下都应启动。

#### Scenario: MySQL 服务启动
- **WHEN** Docker Compose 启动时（无论何种模式）
- **THEN** MySQL 8.0 服务应成功启动并可用

#### Scenario: Backend 服务连接 MySQL
- **WHEN** Backend 服务启动时
- **THEN** 应能够通过 Docker 服务名成功连接到 MySQL 数据库

#### Scenario: MySQL 数据持久化
- **WHEN** MySQL 服务重启
- **THEN** 数据库数据应被保留

#### Scenario: 开发和生产环境支持
- **WHEN** 在开发或生产环境中使用 Docker Compose
- **THEN** MySQL 服务应在两个环境中都可用且配置正确

#### Scenario: MySQL 端口访问
- **WHEN** 用户通过数据库管理工具访问 MySQL（端口 3306）
- **THEN** 应能够成功连接并管理数据库

