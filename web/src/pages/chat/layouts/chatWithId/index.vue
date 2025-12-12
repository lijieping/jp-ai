<!-- 每个回话对应的聊天内容 -->
<script setup lang="ts">
import type { AnyObject } from 'typescript-api-pro';
import type { BubbleProps } from 'vue-element-plus-x/types/Bubble';
import type { BubbleListInstance } from 'vue-element-plus-x/types/BubbleList';
import type { FilesCardProps } from 'vue-element-plus-x/types/FilesCard';
import { useHookFetch } from 'hook-fetch/vue';
import { Sender } from 'vue-element-plus-x';
import { useRoute } from 'vue-router';
import { send } from '@/api';

// import FilesSelect from '@/components/FilesSelect/index.vue';
// import ModelSelect from '@/components/ModelSelect/index.vue';
import { useChatStore } from '@/stores/modules/chat';
import { useFilesStore } from '@/stores/modules/files';
//import { useModelStore } from '@/stores/modules/model';
import { useUserStore } from '@/stores/modules/user';
import { useSessionStore } from '@/stores/modules/session';
import defaultAvatar from '@/assets/images/default-avatar.png'
import agentAvatar from '@/assets/images/agent-avatar.png'

type MessageItem = BubbleProps & {
  key: number;
  role: 'user' | 'assistant';
  avatar: string;
  content: string;
};

const route = useRoute();
const chatStore = useChatStore();
const filesStore = useFilesStore();
const userStore = useUserStore();
const sessionStore = useSessionStore();

// 用户头像
const avatar = computed(() => {
  const userInfo = userStore.userInfo;
  return userInfo?.avatar || defaultAvatar;
});
// ai助手头像
const aiAvatar = computed(() =>  agentAvatar);
const inputValue = ref('');
const senderRef = ref<InstanceType<typeof Sender> | null>(null);
const bubbleItems = ref<MessageItem[]>([]);
const bubbleListRef = ref<BubbleListInstance | null>(null);

const { stream, loading: isLoading, cancel } = useHookFetch({
  request: send,
  onError: (err) => {
    console.warn('测试错误拦截', err);
  },
});

watch(
  () => route.params?.id,
  async (_id_) => {
    if (_id_) {
      // 判断的当前会话id是否有聊天记录，有缓存则直接赋值展示
      if (chatStore.chatMap[`${_id_}`] && chatStore.chatMap[`${_id_}`].length) {
        bubbleItems.value = chatStore.chatMap[`${_id_}`] as MessageItem[];
        // 滚动到底部
        setTimeout(() => {
          bubbleListRef.value!.scrollToBottom();
        }, 350);
        return;
      }

      // 无缓存则请求聊天记录
      await chatStore.requestChatList(`${_id_}`);
      // 请求聊天记录后，赋值回显，并滚动到底部
      bubbleItems.value = chatStore.chatMap[`${_id_}`] as MessageItem[];

      // 滚动到底部
      setTimeout(() => {
        bubbleListRef.value!.scrollToBottom();
      }, 350);

      // 判断会话的首条 ，有则直接发送
      const v = localStorage.getItem('firstChatContent');
      if (v) {
        // 发送消息
        setTimeout(() => {
          startSSE(v);
        }, 350);

        localStorage.removeItem('firstChatContent');
      }
    }
  },
  { immediate: true, deep: true },
);

// 封装数据处理逻辑
function handleDataChunk(frame: AnyObject) {
    // sseTextDecoderPlugin源码：没开启json自动解析，或者开了json自动解析但JSON.parse失败（数据不是json格式），都不会做前缀移除了，这种情况需要调用方自己处理
    const str = frame.slice(5).trim(); //移除'data:'
    bubbleItems.value[bubbleItems.value.length - 1].content += str;
    bubbleItems.value[bubbleItems.value.length - 1].loading = false;

}

// 封装错误处理逻辑
async function handleError(err: any) {
  const detail = await err.response?.json()
  .then((rspJson:any) => (typeof rspJson?.detail === 'string' && rspJson.detail.trim() ? rspJson.detail : '系统错误'))
  .catch(() => '系统错误');
  ElMessage.error(detail);
}

async function startSSE(chatContent: string) {
  try {
    // 添加用户输入的消息
    // console.log('chatContent', chatContent);
    // 清空输入框
    inputValue.value = '';
    // 渲染用户消息
    addMessage(chatContent, true);
    // 添加AI回复的空消息，开始打字器状态
    addMessage('', false);

    // 这里有必要调用一下 BubbleList 组件的滚动到底部 手动触发 自动滚动
    bubbleListRef.value?.scrollToBottom();

    for await (const chunk of stream({
      content : chatContent,
      role: 'user',
      conv_id: route.params?.id !== 'not_login' ? String(route.params?.id) : undefined,
    })) {
      console.log('=====handleDataChunk', chunk.result);
      handleDataChunk(chunk.result as AnyObject);
    }
    // 触发会话标题生成
    sessionStore.triggerGenerateTitle();
  }
  catch (err) {
    handleError(err);
  }
  finally {
    // 停止打字器状态
    bubbleItems.value[bubbleItems.value.length - 1].typing = false;
    // 停止助手loading
    bubbleItems.value[bubbleItems.value.length - 1].loading = false;
    // 停止输入框loading
    isLoading.value = false;
  }
}

// 中断请求
async function cancelSSE() {
  cancel();
  // 结束最后一条消息打字状态
  if (bubbleItems.value.length) {
    bubbleItems.value[bubbleItems.value.length - 1].typing = false;
  }
}

// 添加消息 - 维护聊天记录
function addMessage(message: string, isUser: boolean) {
  const i = bubbleItems.value.length;
  const obj: MessageItem = {
    key: i,
    avatar: isUser ? avatar.value : aiAvatar.value,
    avatarSize: '32px',
    role: isUser ? 'user' : 'assistant',
    placement: isUser ? 'end' : 'start',
    isMarkdown: !isUser,
    loading: !isUser,
    typing: !isUser,
    content: message || ''
  };
  bubbleItems.value.push(obj);
}

// 展开收起 事件展示（暂时注释，如需使用可取消注释）
// function handleChange(payload: { value: boolean; status: ThinkingStatus }) {
//   console.log('value', payload.value, 'status', payload.status);
// }

function handleDeleteCard(_item: FilesCardProps, index: number) {
  filesStore.deleteFileByIndex(index);
}

watch(
  () => filesStore.filesList.length,
  (val) => {
    if (val > 0) {
      nextTick(() => {
        senderRef.value?.openHeader();
      });
    }
    else {
      nextTick(() => {
        senderRef.value?.closeHeader();
      });
    }
  },
);
</script>

<template>
      <div class="chat-warp">
        <BubbleList ref="bubbleListRef" :list="bubbleItems" max-height="calc(100vh - 240px)">
        <!-- <template #header="{ item }">
          <Thinking
            v-if="item.reasoning_content" v-model="item.thinlCollapse" :content="item.reasoning_content"
            :status="item.thinkingStatus" class="thinking-chain-warp" @change="handleChange"
          />
        </template> -->

        <template #content="{ item }">
          <!-- chat 内容走 markdown -->
          <XMarkdown v-if="item.content && item.role === 'assistant'" :markdown="item.content" class="markdown-body" :themes="{ light: 'github-light', dark: 'github-dark' }" default-theme-mode="dark" />
          <!-- user 内容 纯文本 -->
          <div v-if="item.content && item.role === 'user'" class="user-content">
            {{ item.content }}
          </div>
        </template>
      </BubbleList>

      <Sender
        ref="senderRef" v-model="inputValue" class="chat-defaul-sender" :auto-size="{
          maxRows: 6,
          minRows: 2,
        }" variant="updown" clearable :allow-speech="false" :loading="isLoading" @submit="startSSE" @cancel="cancelSSE"
      >
        <template #header>
          <div class="sender-header p-12px pt-6px pb-0px">
            <Attachments :items="filesStore.filesList" :hide-upload="true" @delete-card="handleDeleteCard">
              <template #prev-button="{ show, onScrollLeft }">
                <div
                  v-if="show"
                  class="prev-next-btn left-8px flex-center w-22px h-22px rounded-8px border-1px border-solid border-[rgba(0,0,0,0.08)] c-[rgba(0,0,0,.4)] hover:bg-#f3f4f6 bg-#fff font-size-10px"
                  @click="onScrollLeft"
                >
                  <el-icon>
                    <ArrowLeftBold />
                  </el-icon>
                </div>
              </template>

              <template #next-button="{ show, onScrollRight }">
                <div
                  v-if="show"
                  class="prev-next-btn right-8px flex-center w-22px h-22px rounded-8px border-1px border-solid border-[rgba(0,0,0,0.08)] c-[rgba(0,0,0,.4)] hover:bg-#f3f4f6 bg-#fff font-size-10px"
                  @click="onScrollRight"
                >
                  <el-icon>
                    <ArrowRightBold />
                  </el-icon>
                </div>
              </template>
            </Attachments>
          </div>
        </template>
        <template #prefix>
          <div class="flex-1 flex items-center gap-8px flex-none w-fit overflow-hidden">
            <!-- <FilesSelect /> -->
            <!-- <ModelSelect /> -->
          </div>
        </template>
      </Sender>
    </div>
</template>

<style scoped lang="scss">
.chat-warp {
  display: flex;
  flex-direction: column;
  justify-content: space-between;
  width: 100%;
  max-width: 800px;
  height: calc(100vh - 60px);
  .thinking-chain-warp {
    margin-bottom: 12px;
  }
}

:deep() {
  .el-bubble-list {
    padding-top: 24px;
  }
  .el-bubble {
    padding: 0 12px;
    padding-bottom: 24px;
  }
  .el-typewriter {
    overflow: hidden;
    border-radius: 12px;
  }
  .user-content {
    // 换行
    white-space: pre-wrap;
  }
  .markdown-body {
    background-color: transparent;
  }
  .markdown-elxLanguage-header-div {
    top: -25px !important;
  }

  // xmarkdown 样式
  .elx-xmarkdown-container {
    padding: 8px 4px;
  }
}

.chat-defaul-sender {
  width: 100%;
  margin-bottom: 22px;
}
</style>
