# Change: 添加部署模式并集成可选 Redis 服务

## Why
项目需要支持轻量部署模式，在资源受限环境下运行。Redis 作为缓存和对话记忆存储服务，不是所有部署场景的必需组件。通过引入部署模式（std/lite），可以在标准模式下启用 Redis 等完整功能，在轻量模式下仅运行核心功能，降低资源消耗。

## What Changes
- 添加全局部署模式变量 `MODE`，支持 `std`（标准模式）和 `lite`（轻量模式）
- 在 Docker Compose 配置中添加 Redis 8.4.0 服务，仅在标准模式下启动
- 修改 backend 配置，使 `REDIS_URL` 在轻量模式下可选
- 更新 backend 代码，根据部署模式条件性初始化 Redis 客户端
- 通过环境变量或启动参数指定部署模式，backend 和 Docker Compose 共享该配置
- 更新 `openspec/project.md`，添加 Redis 服务的详细说明

## Impact
- 受影响的基础设施：Docker Compose 配置、Backend 配置系统
- 受影响的文件：
  - `docker-compose.yml` - 添加 Redis 服务和模式条件
  - `docker-compose.dev.yml` - 添加 Redis 服务和模式条件
  - `backend/app/infra/settings.py` - 添加 MODE 配置，使 REDIS_URL 可选
  - `backend/app/infra/redis.py` - 根据模式条件性初始化 Redis
  - `backend/app/infra/agent_memory.py` - 在轻量模式下禁用 Redis 模式
- 新增服务：Redis 8.4.0（仅在标准模式下启动）
- 新增配置：`MODE` 环境变量（std/lite）
- 受影响文档：`openspec/project.md` - 添加 Redis 服务说明

