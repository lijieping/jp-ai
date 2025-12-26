# Design: 部署模式与可选 Redis 集成

## Context
项目需要支持两种部署模式：
- **标准模式（std）**：完整功能，包括 Redis 缓存和对话记忆存储
- **轻量模式（lite）**：核心功能，不包含 Redis，降低资源消耗

当前 Redis 在代码中已被使用，但配置为必需项。需要将其改为可选组件，并根据部署模式条件性启动。

## Goals / Non-Goals

### Goals
- 通过单一环境变量 `MODE` 控制部署模式
- 标准模式下自动启动 Redis 服务
- 轻量模式下系统可在无 Redis 情况下正常运行
- Backend 和 Docker Compose 共享相同的模式配置

### Non-Goals
- 不支持运行时动态切换模式（需重启服务）
- 不改变现有的 Redis 使用方式（仅改变初始化逻辑）

## Decisions

### Decision 1: 使用 Docker Compose Profiles 控制 Redis 启动
**选择**：使用 Docker Compose 的 `profiles` 功能，在标准模式下启用 Redis 8.4.0 服务。

**理由**：
- Docker Compose 原生支持，无需额外脚本
- 清晰的条件启动机制
- 与 `depends_on` 配合良好

**替代方案**：
- 使用环境变量条件启动：需要额外的启动脚本，复杂度更高
- 始终启动但禁用：浪费资源，不符合轻量部署目标

### Decision 2: MODE 环境变量默认值为 lite
**选择**：`MODE` 环境变量默认值为 `lite`（轻量模式）。

**理由**：
- 符合轻量部署的优先原则
- 降低新部署的默认资源消耗
- 明确需要标准模式时必须显式配置

### Decision 3: REDIS_URL 在轻量模式下为可选
**选择**：在 `settings.py` 中将 `REDIS_URL` 改为 `Optional[str]`，在轻量模式下允许为 None。

**理由**：
- 类型安全，明确表达可选性
- 避免在轻量模式下提供无效配置
- 便于代码中条件判断

### Decision 4: Redis 客户端初始化失败处理
**选择**：在轻量模式下，`get_redis_client()` 应返回 None 或抛出明确的异常，禁止在轻量模式下使用 Redis。

**理由**：
- 防止误用 Redis 功能
- 提供清晰的错误信息
- 确保模式约束被正确执行

## Risks / Trade-offs

### Risk 1: 现有代码假设 Redis 始终可用
**缓解措施**：
- 检查所有使用 Redis 的代码路径
- 在轻量模式下禁用 Redis 相关功能（如 `AGENT_MEM_MODE=redis`）
- 添加运行时检查，确保模式一致性

### Risk 2: 配置错误导致服务启动失败
**缓解措施**：
- 在配置加载时进行验证
- 标准模式下必须提供 REDIS_URL
- 提供清晰的错误提示

### Risk 3: Docker Compose Profiles 兼容性
**缓解措施**：
- 使用 Docker Compose v2+ 的 profiles 功能
- 在文档中明确版本要求
- 提供不使用 profiles 的备选方案（如果需要）

## Migration Plan

### 步骤 1: 添加配置和基础设施
1. 在 Docker Compose 中添加 Redis 服务和 MODE 环境变量
2. 使用 profiles 控制 Redis 启动
3. 更新 backend 配置系统

### 步骤 2: 更新代码逻辑
1. 修改 Redis 客户端初始化逻辑
2. 更新 agent_memory 以支持模式检查
3. 添加配置验证

### 步骤 3: 更新项目文档
1. 在 `openspec/project.md` 的"基础设施服务"部分添加 Redis 8.4.0 详细说明
2. 更新 `openspec/project.md` 的"External Dependencies"部分，明确 Redis 版本为 8.4.0
3. 说明 Redis 仅在标准模式下启动

### 步骤 4: 测试和验证
1. 测试标准模式下 Redis 正常启动
2. 测试轻量模式下系统正常运行
3. 验证配置错误时的错误处理

### 回滚计划
- 如果出现问题，可以临时移除 profiles，使 Redis 始终启动
- 将 `REDIS_URL` 改回必需项
- 移除 `MODE` 配置，恢复原有行为

## Open Questions
- [ ] 是否需要在前端也支持模式配置？（当前仅 backend 需要）
- [ ] 轻量模式下是否完全禁用 Redis 相关功能，还是允许连接外部 Redis？（当前设计：完全禁用）

