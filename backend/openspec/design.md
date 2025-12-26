# 系统设计文档

## 架构概览

本项目是一个基于 FastAPI 的 AI Agent 后端系统，采用分层架构设计，支持多 Agent 路由、RAG（检索增强生成）知识库管理和对话管理。

### 整体架构

```
┌─────────────────────────────────────────────────────────┐
│                    FastAPI Application                   │
│  ┌──────────┐  ┌──────────┐  ┌──────────┐  ┌─────────┐ │
│  │   User   │  │Conversation│ │   RAG    │  │  Agent  │ │
│  │   API    │  │    API     │ │   API    │  │  Router │ │
│  └────┬─────┘  └─────┬──────┘  └────┬─────┘  └────┬────┘ │
│       │              │              │              │      │
│  ┌────▼─────────────▼──────────────▼──────────────▼────┐ │
│  │                    Service Layer                      │ │
│  │  UserService │ ConversationService │ KnowledgeService │ │
│  └────┬──────────────────────────────────────────────────┘ │
│       │                                                     │
│  ┌────▼──────────────────────────────────────────────────┐ │
│  │                    DAO Layer                          │ │
│  │  UserDAO │ ConversationDAO │ MessageDAO │ KbSpaceDAO │ │
│  └────┬──────────────────────────────────────────────────┘ │
│       │                                                     │
│  ┌────▼──────────────────────────────────────────────────┐ │
│  │              Infrastructure Layer                      │ │
│  │  MySQL │ Redis │ VectorStore │ Embedding │ OCR │ Log │ │
│  └────────────────────────────────────────────────────────┘ │
└─────────────────────────────────────────────────────────────┘
```

## 核心模块设计

### 1. Agent 路由系统

#### 1.1 架构设计

采用 **Router Agent + Sub Agents** 的二级路由架构：

```
用户请求
   │
   ▼
Router Agent (智能路由决策)
   │
   ├──► DailySubAgent (日常管家)
   ├──► CompanyAffairsAgent (公司管家)
   └──► [其他 Sub Agents...]
```

#### 1.2 核心组件

**BaseSubAgent (抽象基类)**
- 所有子 Agent 必须继承此基类
- 定义抽象方法 `register_to_router()`，子类实现注册逻辑
- 支持基于继承的自动发现机制

**RouterRegistry (注册器)**
- 管理所有子 Agent 的注册信息
- 提供 `auto_register_all_sub_agents()` 方法自动发现并注册所有子类
- 通过 `__subclasses__()` 递归获取所有子类

**RouterGraphManager (路由图管理器)**
- 单例模式，支持显式初始化和延迟初始化
- 在应用启动时通过 `initialize()` 显式初始化
- 自动扫描 `sub_agent` 包并注册所有子 Agent

**RouterService (路由服务)**
- 构建路由决策的 Prompt
- 执行路由逻辑，将请求转发到对应的子 Agent
- 支持流式响应，实时返回 Agent 执行结果

#### 1.3 自动注册机制

1. **包级别自动导入**：`sub_agent/__init__.py` 自动导入所有子模块
2. **类继承发现**：通过 `BaseSubAgent.__subclasses__()` 获取所有子类
3. **自动注册**：调用每个子类的 `register_to_router()` 类方法完成注册

**优势**：
- 新增子 Agent 只需继承 `BaseSubAgent` 并实现注册方法
- 无需手动维护注册列表
- 完全自动化，符合开闭原则

#### 1.4 子 Agent 实现示例

```python
class DailySubAgent(BaseSubAgent):
    @classmethod
    def register_to_router(cls, registry: RouterRegistry):
        service = DailyAgentService()
        agent = service.initialize_agent()
        registry.register(
            id="daily_assistant",
            name="日常管家",
            description="处理生活琐事和简单问答的个人助理",
            trigger_conditions=[...],
            example="...",
            agent=agent
        )
```

### 2. RAG 知识库系统

#### 2.1 架构设计

采用 **责任链模式** 实现文档处理流水线：

```
文件上传
   │
   ▼
FileParseHandler (文件解析)
   │
   ▼
ChunkHandler (文档分块)
   │
   ▼
EmbedAStoreHandler (向量化存储)
   │
   ▼
向量数据库 (FAISS/Chroma)
```

#### 2.2 核心组件

**Handler (抽象处理者)**
- 定义责任链的抽象接口
- 支持链式调用：`handler.set_next(next_handler)`
- 每个 Handler 处理特定阶段的任务

**RagPipelineService (流水线服务)**
- 管理整个文档处理流水线
- 使用线程池异步执行，非阻塞处理
- 支持多种文件格式：PDF、Word、Excel、图片等

**KnowledgeService (知识库服务)**
- 管理知识库空间（KbSpace）和文件（KbFile）
- 提供知识库的 CRUD 操作
- 与向量数据库集成

#### 2.3 向量存储

支持两种向量存储模式（通过配置切换）：
- **FAISS**：本地文件存储，轻量模式
- **Chroma**：独立服务，标准模式

### 3. 对话管理系统

#### 3.1 架构设计

```
用户消息
   │
   ▼
ConversationService
   │
   ├──► Agent Router (路由到对应 Agent)
   │
   ├──► 流式响应处理
   │
   └──► 消息持久化 (MySQL)
```

#### 3.2 核心组件

**ConversationService (对话服务)**
- 处理用户消息的创建和查询
- 集成 Agent Router，将消息路由到对应 Agent
- 支持流式响应，实时返回 Agent 执行结果
- 消息持久化到数据库

**MessageDAO (消息数据访问)**
- 管理对话消息的数据库操作
- 支持按对话 ID 查询消息列表
- 消息类型：USER、AI、ROUTER、TOOL

### 4. 基础设施层

#### 4.1 管理器模式

采用 **Manager 模式** 管理基础设施组件，支持延迟初始化：

**MySQLManager**
- 延迟初始化数据库连接
- 提供 `engine`、`DbSession`、`Base` 属性
- 支持显式初始化：`mysql_manager.initialize()`

**RouterGraphManager**
- 管理 Router Graph 的创建和初始化
- 支持显式初始化和延迟初始化
- 自动注册所有子 Agent

#### 4.2 配置管理

**Settings (配置类)**
- 使用 Pydantic Settings 管理配置
- 支持环境变量和配置文件
- 通过 `get_settings()` 获取配置实例（LRU 缓存）

**部署模式**：
- **lite 模式**：轻量部署，使用 FAISS 本地向量存储
- **std 模式**：标准部署，使用 Chroma/Redis 等外部服务

#### 4.3 其他基础设施

- **Embedding**：支持多种 Embedding 模型（BGE、FastEmbed 等）
- **OCR**：支持多种 OCR 引擎（Buyan、EasyOCR）
- **日志**：统一的日志管理
- **文件存储**：本地文件存储管理

## 设计模式

### 1. 分层架构 (Layered Architecture)

- **API 层**：FastAPI 路由，处理 HTTP 请求
- **Service 层**：业务逻辑，依赖注入 DAO
- **DAO 层**：数据访问，封装数据库操作
- **Infra 层**：基础设施，可复用的底层组件

### 2. 依赖注入 (Dependency Injection)

Service 层通过构造函数接收 DAO 实例：

```python
class ConversationService:
    def __init__(self, conv_dao: ConvDAO, msg_dao: MsgDAO):
        self.conv_dao = conv_dao
        self.msg_dao = msg_dao
```

### 3. 单例模式 (Singleton Pattern)

基础设施组件使用单例模式：
- `mysql_manager`：全局 MySQL 管理器
- `router_graph_manager`：全局 Router Graph 管理器

### 4. 工厂模式 (Factory Pattern)

统一响应包装：

```python
R.ok(data=result)  # 成功响应
R.fail(msg="error")  # 失败响应
```

### 5. 策略模式 (Strategy Pattern)

Agent 路由系统：
- Router Agent 根据用户请求选择不同的 Sub Agent
- 每个 Sub Agent 实现不同的处理策略

### 6. 模板方法模式 (Template Method Pattern)

BaseSubAgent 定义注册模板，子类实现具体注册逻辑。

### 7. 责任链模式 (Chain of Responsibility)

RAG 文档处理流水线：
- 每个 Handler 处理特定阶段
- 通过 `set_next()` 链式连接
- 支持流水线式处理

### 8. Manager 模式

基础设施组件使用 Manager 模式：
- 延迟初始化
- 显式初始化控制
- 统一管理资源

## 初始化顺序

应用启动时遵循严格的初始化顺序（在 `main.py` 中显式控制）：

1. **配置和环境变量**：`init_settings()`
2. **日志系统**：`init_logger()`
3. **基础组件**：`mysql_manager.initialize()`
4. **Agent 路由系统**：`router_graph_manager.initialize()`
5. **FastAPI 应用**：创建 FastAPI 实例
6. **中间件**：添加认证中间件
7. **业务路由**：注册各个业务模块的路由

**设计原则**：显式控制初始化顺序，避免隐式依赖问题。

## 数据流

### 用户消息处理流程

```
1. 用户发送消息
   │
   ▼
2. ConversationAPI.message_post()
   │
   ▼
3. ConversationService.message_create()
   │
   ├──► Agent Router 路由决策
   │
   ├──► Sub Agent 执行
   │
   ├──► 流式返回结果
   │
   └──► 消息持久化
```

### 文档处理流程

```
1. 用户上传文件
   │
   ▼
2. KnowledgeAPI 接收文件
   │
   ▼
3. RagPipelineService 提交处理任务
   │
   ├──► FileParseHandler 解析文件
   │
   ├──► ChunkHandler 文档分块
   │
   ├──► EmbedAStoreHandler 向量化
   │
   └──► 存储到向量数据库
```

## 技术栈

### 核心框架
- **FastAPI**：Web 框架
- **LangChain**：LLM 应用框架
- **LangGraph**：Agent 工作流框架
- **SQLAlchemy**：ORM 框架
- **Pydantic**：数据验证

### AI/ML 相关
- **DashScope**：阿里云百炼 API
- **FAISS**：向量相似度搜索
- **Chroma**：向量数据库
- **FastEmbed**：Embedding 模型

### 数据库
- **MySQL**：关系型数据库
- **Redis**：缓存和 Agent 记忆存储（可选）

### 其他
- **Uvicorn**：ASGI 服务器
- **PyJWT**：JWT 认证
- **bcrypt**：密码加密

## 扩展性设计

### 添加新的 Sub Agent

1. 在 `app/agent/sub_agent/` 目录下创建新文件
2. 定义类继承 `BaseSubAgent`
3. 实现 `register_to_router()` 类方法
4. 系统会自动发现并注册

### 添加新的文档格式支持

1. 在 `RagPipelineService` 中添加新的 Handler
2. 在 `FileParseHandler._support_exts` 中注册文件扩展名
3. 实现对应的解析逻辑

### 切换向量存储后端

通过配置 `VECTOR_STORE_MODE` 切换：
- `faiss`：使用 FAISS
- `chroma`：使用 Chroma

## 性能优化

1. **延迟初始化**：基础设施组件支持延迟初始化，避免启动时加载所有资源
2. **异步处理**：RAG 流水线使用线程池异步处理，非阻塞
3. **流式响应**：Agent 执行结果流式返回，提升用户体验
4. **连接池**：数据库连接使用连接池管理
5. **LRU 缓存**：配置读取使用 LRU 缓存

## 安全设计

1. **JWT 认证**：使用 JWT Token 进行 API 认证
2. **密码加密**：使用 bcrypt 加密用户密码
3. **中间件保护**：通过 AuthMiddleware 统一处理认证
4. **访客控制**：支持访客用户概率性访问控制

## 部署模式

### Lite 模式（轻量模式）
- 使用 FAISS 本地向量存储
- 无需外部 Redis 服务
- 适合单机部署

### Std 模式（标准模式）
- 使用 Chroma 向量数据库
- 支持 Redis 缓存
- 适合分布式部署

