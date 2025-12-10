import type { ChatMessageVo } from '@/api/chat/types';
import { defineStore } from 'pinia';
import { getChatList } from '@/api';
import { useUserStore } from './user';
import defaultAvatar from '@/assets/images/default-avatar.png'
import agentAvatar from '@/assets/images/agent-avatar.png'

export const useChatStore = defineStore('chat', () => {
  const userStore = useUserStore();

  // 用户头像
  const avatar = computed(() => {
    const userInfo = userStore.userInfo;
    return userInfo?.avatar || defaultAvatar;
  });
  // ai头像
  const aiAvatar = computed(() => agentAvatar);

  // 是否开启深度思考
  const isDeepThinking = ref<boolean>(false);

  const setDeepThinking = (value: boolean) => {
    isDeepThinking.value = value;
  };

  // 会议ID对应-聊天记录 map对象
  const chatMap = ref<Record<string, ChatMessageVo[]>>({});

  const setChatMap = (id: string, data: ChatMessageVo[]) => {
    chatMap.value[id] = data?.map((item: ChatMessageVo) => {
      const isUser = item.role === 'user';
      const thinkContent = extractThkContent(item.content as string);
      return {
        ...item,
        key: item.id,
        placement: isUser ? 'end' : 'start',
        isMarkdown: !isUser,
        // variant: 'shadow',
        // shape: 'corner',
        avatar: isUser? avatar.value : aiAvatar.value,
        avatarSize: '32px',
        typing: false,
        reasoning_content: thinkContent,
        thinkingStatus: 'end',
        content: extractThkContentAfter(item.content as string),
        thinlCollapse: false,
      };
    });
  };

  // 获取当前会话的聊天记录
  const requestChatList = async (sessionId: string) => {
    try {
      const res = await getChatList({
        sessionId,
        userId: userStore.userInfo?.userId as number,
      });
      if (res.data) {
        setChatMap(sessionId, res.data);
      }
    }
    catch (error) {
      console.error('getChatList:', error);
    }
  };

  // 对思考中的内容回显做处理
  function extractThkContent(content: string) {
    const regex = /<think>(.*?)<\/think>/s;
    const matchResult = content.match(regex);
    // 把这些内容从 content 中移除
    content = content.replace(regex, '');
    return matchResult?.[1] ?? '';
  }

  // 如果有 </think> 标签，则把 </think> 之后的 内容从 content 中返回
  function extractThkContentAfter(content: string) {
    if (!content.includes('</think>')) {
      return content;
    }
    const regex = /<\/think>(.*)/s;
    const matchResult = content.match(regex);
    // 把这些内容从 content 中移除
    content = content.replace(regex, '');
    return matchResult?.[1] ?? '';
  }

  return {
    chatMap,
    requestChatList,
    isDeepThinking,
    setDeepThinking,
  };
});
