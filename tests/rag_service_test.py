from app.service import rag_service

print(rag_service.query_lite_mode("index_2", "技术亮点", 3))