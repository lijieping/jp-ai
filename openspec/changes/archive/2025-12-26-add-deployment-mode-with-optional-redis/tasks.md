## 1. 配置和基础设施
- [x] 1.1 在 `docker-compose.yml` 中添加 Redis 8.4.0 服务定义
- [x] 1.2 在 `docker-compose.yml` 中添加 `MODE` 环境变量配置
- [x] 1.3 配置 Redis 服务仅在标准模式下启动（使用 profiles 或条件启动）
- [x] 1.4 在 `docker-compose.dev.yml` 中同步添加 Redis 8.4.0 服务配置
- [x] 1.5 更新 backend 服务的 `depends_on`，使其在标准模式下依赖 Redis

## 2. Backend 配置系统
- [x] 2.1 在 `backend/app/infra/settings.py` 中添加 `MODE` 配置项（默认值：lite）
- [x] 2.2 修改 `REDIS_URL` 配置，使其在轻量模式下可选（Optional[str]）
- [x] 2.3 添加配置验证逻辑，确保标准模式下 REDIS_URL 必须提供

## 3. Backend Redis 集成
- [x] 3.1 修改 `backend/app/infra/redis.py`，在轻量模式下返回 None 或抛出明确异常
- [x] 3.2 更新 `backend/app/infra/agent_memory.py`，在轻量模式下禁用 Redis 模式选择
- [x] 3.3 确保所有使用 Redis 的代码能够优雅处理 Redis 不可用的情况

## 4. 文档和测试
- [x] 4.1 更新 `openspec/project.md`，在"基础设施服务"部分添加 Redis 8.4.0 详细说明
- [x] 4.2 更新 `openspec/project.md`，在"External Dependencies"部分明确 Redis 版本为 8.4.0
- [x] 4.3 更新项目文档，说明部署模式的使用方法
- [ ] 4.4 验证标准模式下 Redis 服务正常启动和连接
- [ ] 4.5 验证轻量模式下系统可以在无 Redis 情况下正常运行

