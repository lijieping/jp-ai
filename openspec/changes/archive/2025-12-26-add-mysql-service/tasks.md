## 1. 实现任务
- [x] 1.1 在 docker-compose.yml 中添加 MySQL 8.0 服务配置
- [x] 1.2 在 docker-compose.dev.yml 中添加 MySQL 8.0 服务配置
- [x] 1.3 配置 MySQL 数据持久化（使用 Docker 卷挂载）
- [x] 1.4 配置 MySQL 默认数据库、用户名和密码
- [x] 1.5 更新 backend 服务的 MYSQL_URL 环境变量（从外部地址改为 Docker 服务名）
- [x] 1.6 配置 backend 服务依赖 MySQL 服务（depends_on）
- [x] 1.7 验证 MySQL 服务可以正常启动和连接
- [x] 1.8 更新 `openspec/project.md`，将 MySQL 8.0 从"外部服务"移动到"基础设施服务"

