import type { ChatMessageVo, GetChatListParams, SendDTO } from './types';
import { get, post } from '@/utils/request';

// 发送消息
export const send = (data: SendDTO) => post<null>('/conversation/' + data.sessionId + '/message', data);

// 获取当前会话的聊天记录
export function getChatList(params: GetChatListParams) {
  return get<ChatMessageVo[]>('/conversation/' + params.sessionId + '/message/list', params).json();
}
