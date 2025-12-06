# 官方 Python 镜像
FROM python:3.13-slim AS builder

# 配置pip源
RUN pip config set global.index-url https://pypi.tuna.tsinghua.edu.cn/simple

#安装 uv 包管理器
RUN pip install uv
ENV UV_PYTHON_VERSION=3.13

# 设置工作目录[citation:2]
WORKDIR /app

# 仅复制依赖声明文件
COPY pyproject.toml uv.lock ./

# 启用缓存并安装依赖，使用 `--mount=type=cache` 可以显著加速后续的构建过程
RUN --mount=type=cache,target=/root/.cache/uv \
    --mount=type=bind,source=uv.lock,target=uv.lock \
    --mount=type=bind,source=pyproject.toml,target=pyproject.toml \
    uv sync --frozen --no-dev --no-install-project

# 复制项目源代码和必要的配置文件
# 复制主应用代码
COPY app ./app
# 复制配置文件目录（如果存在且需要）
#COPY ./config ./config
# 如果有其他必须的目录，按需添加，例如：
# COPY ./scripts ./scripts # 复制脚本目录

# 同步项目依赖
RUN --mount=type=cache,target=/root/.cache/uv \
    uv sync --frozen --no-dev

# 声明容器对外端口
EXPOSE 9000

# 启动应用[citation:2]
CMD ["uv", "run", "uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "9000"]