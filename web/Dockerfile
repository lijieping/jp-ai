# 使用Node.js镜像作为基础（与本地开发环境保持一致）
FROM node:24.11.1-alpine

# 设置工作目录
WORKDIR /app

# 安装pnpm（使用国内镜像源）
RUN npm install -g pnpm --registry=https://registry.npmmirror.com

# 复制依赖文件
COPY package.json pnpm-lock.yaml ./

# 安装依赖（使用国内镜像源）
RUN pnpm config set registry https://registry.npmmirror.com && pnpm install

# 复制项目文件
COPY . .

# 构建项目
RUN pnpm run build

# 暴露端口（Vite preview默认使用4173端口）
EXPOSE 4173

# 启动应用
CMD ["pnpm", "preview", "--host", "0.0.0.0"]