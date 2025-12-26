# jp-ai

一个基于 LangGraph 的 AI Agent 系统，集成 RAG 知识库能力，支持轻量部署和灵活扩展。

## 项目概述

本项目探索了现代 AI Agent 系统的工程化实践，在 LangGraph 框架基础上构建了多 Agent 路由架构，并集成了完整的 RAG（检索增强生成）能力。系统设计时考虑了不同部署场景的资源约束，支持从轻量单机到标准分布式部署的平滑切换。

### 核心特性

- **多 Agent 路由架构**：基于 LangGraph 实现的 Router Agent + Sub Agents 二级路由系统，支持动态注册和扩展
- **RAG 知识库**：完整的文档解析、向量化、检索流程，支持 FAISS/Chroma 双引擎切换
- **对话记忆管理**：基于 LangGraph Checkpoint 机制，支持内存/MySQL/Redis 多种持久化策略
- **灵活部署模式**：标准模式（std）和轻量模式（lite），适配不同资源环境
- **工程化实践**：Monorepo 结构、Docker Compose 多环境配置、OpenSpec 规范管理

## 技术架构

### Agent 系统

采用 **Router Agent + Sub Agents** 架构模式：

```
用户请求 → Router Agent（路由决策）→ Sub Agent（具体执行）
```

- **Router Agent**：基于 LangGraph StateGraph 实现，通过自动扫描机制发现并注册所有 Sub Agents
- **Sub Agents**：继承 `BaseSubAgent` 基类，实现自动注册和路由匹配
- **Checkpoint 机制**：支持 InMemory/MySQL/Redis 三种持久化方式，确保 Agent 状态可恢复

### RAG 系统

- **文档处理**：支持 PDF、Word、Excel、PPT、Markdown 等多种格式
- **向量化**：基于 `bge-small-en-v1.5` 模型，支持 ONNX 量化推理
- **向量存储**：FAISS（本地文件）和 Chroma（远程服务）双引擎，可按需切换
- **检索策略**：相似度检索 + 元数据过滤

### 技术栈

**后端**
- Python 3.13 + FastAPI
- LangChain 1.0 + LangGraph（Agent 框架）
- SQLAlchemy 2.0（ORM）
- FAISS/Chroma（向量数据库）
- MySQL 8.0（数据持久化）
- Redis 8.4（可选，Agent 记忆存储）

**前端**
- Vue 3 + TypeScript
- Element Plus

**基础设施**
- Docker Compose（服务编排）
- uv（Python 包管理）

## 项目结构

```
jp-ai/
├── backend/              # Python FastAPI 后端
│   ├── app/
│   │   ├── agent/        # Agent 路由系统
│   │   │   ├── router_agent.py      # Router Agent 实现
│   │   │   └── sub_agent/           # Sub Agents
│   │   ├── rag/          # RAG 知识库模块
│   │   ├── conversation/ # 对话管理
│   │   └── infra/        # 基础设施层（向量存储、OCR、Embedding）
│   └── pyproject.toml
├── web/                  # Vue 前端
├── docker-compose.yml     # 基础配置
├── docker-compose.dev.yml # 开发环境配置
└── openspec/             # 项目规范文档
```

## 部署

### 环境要求

- Docker & Docker Compose
- Python 3.13（本地开发）
- Node.js 24+（前端开发）

### 快速开始

```bash
# 开发环境
make updev      # 启动服务
make downdev    # 停止服务
make builddev   # 构建镜像

# 生产环境
make upprod     # 启动服务
make downprod   # 停止服务
```

### 部署模式

通过 `MODE` 环境变量控制部署模式：

- **lite（轻量模式）**：默认模式，不启动 Redis，适合资源受限环境
- **std（标准模式）**：完整功能，包括 Redis 缓存和 Agent 记忆持久化

```bash
MODE=std docker compose -f docker-compose.yml -f docker-compose.dev.yml up -d
```

### 配置说明

主要环境变量：

- `VECTOR_STORE_MODE`: `faiss` 或 `chroma`
- `AGENT_MEM_MODE`: `memory`、`mysql` 或 `redis`
- `MODE`: `lite` 或 `std`
- `DASHSCOPE_API_KEY`: 阿里云百炼 API Key

详细配置见 `docker-compose.yml` 和 `docker-compose.dev.yml`。

## 开发

### 后端开发

```bash
cd backend
uv sync                    # 安装依赖
uvicorn app.main:app --reload  # 启动开发服务器
```

### 前端开发

```bash
cd web
pnpm install
pnpm dev
```

### 添加新的 Sub Agent

1. 在 `backend/app/agent/sub_agent/` 创建新文件
2. 继承 `BaseSubAgent` 并实现 `register()` 方法
3. 系统会自动发现并注册

示例：

```python
from app.agent.router_agent import BaseSubAgent

class MySubAgent(BaseSubAgent):
    @classmethod
    def register(cls):
        cls._register(
            id="my_agent",
            name="我的 Agent",
            description="处理特定任务",
            trigger_conditions=["关键词"],
            example="示例对话"
        )
```

## 技术亮点

### 1. Agent 路由系统

- 基于元类机制实现自动注册，新增 Agent 无需修改路由代码
- 支持动态触发条件匹配和示例引导
- 利用 LangGraph 的 Checkpoint 机制实现状态持久化

### 2. 灵活的向量存储

- 抽象向量存储接口，支持多引擎切换
- FAISS 模式支持本地文件持久化，适合单机部署
- Chroma 模式支持远程服务，适合分布式场景

### 3. 工程化实践

- **Monorepo 结构**：统一管理前后端和基础设施
- **多环境配置**：通过 Docker Compose 文件组合实现环境隔离
- **规范管理**：OpenSpec 目录管理项目变更和规范文档
- **部署模式**：通过 profiles 机制实现服务按需启动

### 4. RAG 流程优化

- 文档解析支持 OCR（卟言 API + EasyOCR 双引擎）
- 向量化支持 ONNX 量化模型，降低推理成本
- 检索结果支持元数据过滤和相似度排序

## 演示

在线体验：http://117.72.39.0/

## 外部依赖

- **阿里云百炼 API**：大语言模型服务
- **卟言 OCR API**：中文 OCR 识别（https://qaqbuyan.com:88/api/）
- **Chroma**：向量数据库服务（可选）

## 许可证

MIT

---

*本项目是个人在 AI Agent 技术领域的探索实践，持续迭代中。*
