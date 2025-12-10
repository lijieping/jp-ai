import type {
  ChatSessionVo,
  CreateSessionDTO,
  // CreateSessionVO,
  GetSessionListParams,
} from './types';
import { del, get, post, put } from '@/utils/request';

export function get_session_list(params: GetSessionListParams) {
  return get<ChatSessionVo[]>('/conversation/page', params).json();
}

export function create_session(data: CreateSessionDTO) {
  return post('/conversation', data).json();
}

export function update_session(data: ChatSessionVo) {
  return put('/conversation/' + data.conv_id, data).json();
}

export function get_session(id: string) {
  return get<ChatSessionVo>(`/conversation/${id}`).json();
}

export function delete_session(ids: string[]) {
  return del(`/conversation/${ids}`).json();
}

export function generate_session_title(sessionId: string) {
  return post(`/conversation/${sessionId}/title`).json();
}
