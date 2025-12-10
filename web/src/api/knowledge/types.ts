export interface BizSpaceVO {
  id?: number;
  name: string;
  collection: string;
  desc: string;
}

export interface KnowledgeFileVO {
  id?: number;
  file_name: string;
  file_type: string;
  file_size: number;
  file_url: string;
  created_at: string;
  user_id: number;
  user_name: string;
  space_id: number;
  space_name: string;
  collection: string;
  desc: string;
  description?: string; // 添加description字段
  status: number; // 文件状态，0-失效 1-有效
  rag_status: number; // RAG处理状态，0-待执行 1-成功 2-失败
  msg?: string | null; // RAG处理消息
}

export interface KnowledgeFileParams {
  pageSize: number;
  curPage: number;
  spaceId?: number;
}