# Project Context

## Purpose
AI 对话系统 + 知识库 RAG 项目，支持在有限资源下进行轻量部署。项目采用单体仓库（monorepo）结构，包含前端、后端和基础设施服务。

## Project Structure

### Monorepo 组织
项目采用单体仓库结构，根目录包含：
- **子项目目录**：`backend/`、`web/` 等子项目，每个子项目有独立的实现和配置
- **部署配置**：Docker Compose 配置文件，用于统一管理服务部署
- **构建脚本**：Makefile 提供统一的构建和部署命令
- **规范文档**：OpenSpec 规范目录，用于管理项目变更和规范

### 根目录关键文件
- `docker-compose.yml` - 生产环境 Docker Compose 基础配置
- `docker-compose.dev.yml` - 开发环境 Docker Compose 配置
- `docker-compose.prod.yml` - 生产环境 Docker Compose 配置（如存在）
- `Makefile` - 构建和部署脚本
- `README.md` - 项目说明文档
- `openspec/` - OpenSpec 规范目录
  - `project.md` - 本文件，项目上下文说明
  - `AGENTS.md` - AI 助手工作规范
  - `specs/` - 当前规范（已实现的功能）
  - `changes/` - 变更提案（待实现的功能）

## Docker Deployment

### 部署架构
项目使用 Docker Compose 管理多个服务：
- **backend** - Python FastAPI 后端服务（需构建）
- **web** - Vue/TypeScript 前端服务（需构建）
- **redis** - 缓存和对话记忆存储服务（使用官方镜像，仅在标准模式下启动）

### 部署模式
项目支持两种部署模式，通过 `MODE` 环境变量控制：
- **标准模式（std）**：完整功能，包括 Redis 缓存和对话记忆存储
- **轻量模式（lite）**：核心功能，不包含 Redis，降低资源消耗（默认模式）

### 多文件组合部署
项目采用多文件组合部署方式：
- **基础配置**：`docker-compose.yml` 定义服务的基础结构和通用配置
- **环境配置**：`docker-compose.dev.yml` 或 `docker-compose.prod.yml` 提供环境特定配置
- **组合使用**：通过 `docker compose -f` 参数组合多个 compose 文件

优势：
- 保持基础配置的通用性
- 通过环境特定文件覆盖配置（如数据库连接、服务地址）
- 便于管理不同环境的差异

### 基础设施服务

#### MySQL
- **版本**：8.0
- **镜像**：`mysql:8.0`
- **端口**：3306（标准 MySQL 端口）
- **数据持久化**：通过 Docker 卷挂载 data 和 logs 目录
- **默认数据库**：`ai_agent`
- **字符集**：utf8mb4
- **连接方式**：Backend 服务通过 Docker 服务名 `mysql` 连接
- **用途**：应用数据存储

#### Redis
- **版本**：8.4.0
- **镜像**：`redis:8.4.0`
- **端口**：6379（标准 Redis 端口）
- **数据持久化**：通过 Docker 卷挂载 data 目录
- **部署模式**：仅在标准模式（`MODE=std`）下启动
- **连接方式**：Backend 服务通过 Docker 服务名 `redis` 连接
- **用途**：缓存服务、对话记忆存储（Agent Memory）

### 部署命令

通过 Makefile 提供的快捷命令：

**开发环境**：
- `make updev` - 启动开发环境服务
- `make downdev` - 停止开发环境服务
- `make builddev` - 构建开发环境镜像
- `make redev` - 完全重建并启动（清理旧镜像）

**生产环境**：
- `make upprod` - 启动生产环境服务
- `make downprod` - 停止生产环境服务
- `make buildprod` - 构建生产环境镜像
- `make reprod` - 完全重建并启动（清理旧镜像）

## Project Conventions

### 工作原则
在处理根目录层级的内容时：
1. **只关注根目录层级** - 重点关注部署、构建相关的根目录文件
2. **不深入子项目** - 不在此层级深入 `backend/` 或 `web/` 子项目的内部实现细节
3. **关注部署配置** - 重点关注 Docker Compose 配置、Makefile 等部署和构建相关文件
4. **理解项目结构** - 理解这是一个多子项目的单体仓库（monorepo）结构

### 子项目规范
- 每个子项目（如 `backend/`、`web/`）应有自己的 `project.md` 或类似文档
- 子项目的技术栈、代码风格、架构模式等应在子项目文档中说明
- 根目录的 `project.md` 只关注根目录层级的部署和项目结构

## Important Constraints

### 部署约束
- 项目支持轻量部署，可在有限资源下运行
- 使用 Docker Compose 统一管理服务生命周期
- 数据持久化通过 Docker 卷挂载实现

### 环境差异
- 开发环境和生产环境使用不同的配置文件
- 环境变量、数据库连接、服务地址等通过环境配置文件覆盖
- 卷挂载路径在不同环境中可能不同（如开发环境使用 `/mnt/e/`，生产环境使用 `/data/`）

## External Dependencies

### 基础设施服务（通过 Docker Compose 管理）
- **MySQL 8.0** - 数据库服务
- **Redis 8.4.0** - 缓存服务、对话记忆存储（仅在标准模式下启动）

### 外部服务（通过环境变量配置连接）
- **Chroma/FAISS** - 向量数据库
- **阿里云百炼 API** - AI 模型服务
- **卟言 OCR API** - OCR 服务
