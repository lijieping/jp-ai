# jp-ai
# 介绍
AI对话系统+知识库RAG，目前两个模式  
- lite模式：轻量化部署，MySQL+faiss+fastembed+本地内存记忆（定时清理），在2G 4核CPU模式可流畅运行。  
- std模式：标准部署，MySQL+chromadb+BGE-M3+Redis短期记忆，需要合格的GPU环境


# 演示地址：
- 配套前端代码：https://github.com/lijieping/jp-ai-web
- 体验地址：http://117.72.39.0/ 

# 环境
## server
- 阿里云百炼通义千问api  
- mysql 8.0  
- python 3.13.0  
- uv  
- ocr模型：easyocr，语言：zh_sim_g2  
- embedding模型：qdrant/bge-small-en-v1.5-onnx-q  
- redis 8.x (非必须)
## web
- node.js+npm：v24.11.1

# 部署

