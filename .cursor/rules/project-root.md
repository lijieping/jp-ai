# 项目根目录说明

## 项目概述

这是大型项目的根目录，包含多个子项目和部署配置文件。项目类型为 **AI 对话系统 + 知识库 RAG**，支持在有限资源下进行轻量部署。

## 根目录结构

### 子项目文件夹

- **`backend/`** - Python 后端子项目
  - 包含 AI 对话、知识库 RAG 等后端服务
  - 使用 FastAPI 框架
  - 不在此层级深入子项目内部实现细节

- **`web/`** - Vue/TypeScript 前端子项目
  - 基于 ruoyi-element-ai 开发
  - 包含聊天界面、知识库管理等前端功能
  - 不在此层级深入子项目内部实现细节

### 部署配置文件

- **`docker-compose.yml`** - 生产环境 Docker Compose 基础配置
  - 定义服务：backend、web、nacos
  - 包含服务的基础配置、环境变量、卷挂载等
  - 作为基础配置文件，可与其他环境配置文件组合使用

- **`docker-compose.dev.yml`** - 开发环境 Docker Compose 配置
  - 覆盖或扩展基础配置中的开发环境特定设置
  - 包含开发环境的数据库连接、服务地址等配置
  - 通过 `-f` 参数与基础配置组合使用

### 基础设施服务

- **Nacos** - 服务注册与发现、配置管理中间件
  - 版本：3.1.1
  - 镜像：`nacos/nacos-server:v3.1.1`
  - 运行模式：单机模式（standalone）
  - 控制台端口：8848（HTTP API 和管理界面）
  - gRPC 端口：9848（服务注册与发现）
  - 用途：服务注册与发现、动态配置管理、服务治理
  - 数据存储：嵌入式 Derby 数据库（单机模式）
  - 数据持久化：通过 Docker 卷挂载 logs 和 data 目录
  - 默认登录：用户名 `nacos`，密码 `nacos`

### 构建和部署脚本

- **`Makefile`** - 项目构建和部署脚本
  - 提供开发和生产环境的快捷命令
  - 主要命令：
    - `make updev` / `make upprod` - 启动开发/生产环境
    - `make downdev` / `make downprod` - 停止开发/生产环境
    - `make builddev` / `make buildprod` - 构建开发/生产环境镜像
    - `make redev` / `make reprod` - 完全重建并启动（清理旧镜像）
  - 使用 `docker compose -f` 参数组合多个 compose 文件

### 文档文件

- **`README.md`** - 项目说明文档
  - 包含项目介绍、环境要求、部署说明等

- **`.cursor/rules/`** - Cursor AI 规则目录
  - 存放项目特定的 AI 助手规则文件
  - 本文件即位于此目录

## 工作原则

在处理根目录层级的内容时：

1. **只关注根目录层级** - 重点关注部署、构建相关的根目录文件
2. **不深入子项目** - 不在此层级深入 `backend/` 或 `web/` 子项目的内部实现细节
3. **关注部署配置** - 重点关注 Docker Compose 配置、Makefile 等部署和构建相关文件
4. **理解项目结构** - 理解这是一个多子项目的单体仓库（monorepo）结构

## Docker Compose 使用说明

项目使用多文件组合部署方式：

- **基础配置**：`docker-compose.yml` 定义服务的基础结构
- **环境配置**：`docker-compose.dev.yml` 或 `docker-compose.prod.yml` 提供环境特定配置
- **组合使用**：通过 `docker compose -f docker-compose.yml -f docker-compose.dev.yml up -d` 组合使用

这种方式可以：
- 保持基础配置的通用性
- 通过环境特定文件覆盖配置
- 便于管理不同环境的差异

