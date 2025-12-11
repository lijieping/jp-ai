# jp-ai
# 介绍
AI对话系统+知识库RAG，支持在有限资源下进行轻量部署，目前支持的选项：   
- 对话记忆的热存储部分：内存（定时清理） or Redis 
- 向量数据库： faiss（功能受限） or chroma


# 演示地址：
- 体验地址：http://117.72.39.0/ 

# 环境
## backend（后台）
- 阿里云百炼通义千问api  
- mysql 8.0  
- python 3.13.0  
- uv  
- 卟言ocr api：https://qaqbuyan.com:88/api/， 实测响应速度和中文识别质量效果优于easyocr，作者：https://github.com/qaqbuyan
- ocr模型：easyocr，语言：zh_sim_g2  
- embedding模型：qdrant/bge-small-en-v1.5-onnx-q  
- redis 8.x (非必须)
## web（前端，非原创，基于ruoyi-element-ai开发）
- node.js+npm：v24.11.1

# 部署

