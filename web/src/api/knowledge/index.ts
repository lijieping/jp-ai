import type { BizSpaceVO, KnowledgeFileParams, KnowledgeFileVO } from './types';
import { get, post, put, del, postFile } from '@/utils/request';

// 新增业务空间
export function addBizSpace(data: BizSpaceVO) {
  return post('/kb/space', data).json();
}

// 获取所有业务空间
export function listAllBizSpaces() {
  return get<BizSpaceVO[]>('/kb/space/list').json();
}

// 根据ID获取业务空间
export function getBizSpaceById(id: number) {
  return get(`/kb/space/${id}`).json();
}

// 更新业务空间
export function updateBizSpace(id: number, data: Partial<BizSpaceVO>) {
  return put(`/kb/space/${id}`, data).json();
}

// 上传文件到业务空间
export function uploadFilesToBizSpace(spaceId: number, files: FileList | File[], description?: string) {
  const formData = new FormData();
  // 将所有文件添加到FormData
  if (files instanceof FileList) {
    for (let i = 0; i < files.length; i++) {
      formData.append('files', files[i]);
    }
  } else {
    files.forEach(file => {
      formData.append('files', file);
    });
  }
  
  // 如果提供了description，添加到FormData
  if (description) {
    formData.append('description', description);
  }
  
  return postFile(`/kb/space/${spaceId}/file`, formData).json();
}

// 获取知识库文件列表
export function getKnowledgeFileList(params:KnowledgeFileParams) {
  return get<KnowledgeFileVO[]>(`/kb/file/list`, params).json();
}

// 执行RAG检索
export function executeRagRetrieve(data: { file_id: number }) {
  return post(`/kb/rag/pipeline/execute`, data).json();
}

// 获取rag支持的文件类型
export function getSupportedFileTypes() {
  return get<string[]>('/kb/rag/pipeline/file-types').json();
}

// 删除文件
export function deleteKnowledgeFile(fileId: number) {
  return del(`/kb/file/${fileId}`).json();
}