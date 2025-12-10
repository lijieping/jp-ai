<script setup lang="ts">
import { useRoute } from 'vue-router';
import ChatDefaul from '@/pages/chat/layouts/chatDefaul/index.vue';
import ChatWithId from '@/pages/chat/layouts/chatWithId/index.vue';
import { useDesignStore } from '@/stores/modules/design';
import { computed } from 'vue';
import { onKeyStroke } from '@vueuse/core';
import { useSessionStore } from '@/stores/modules/session';
import TitleEditing from '@/pages/chat/layouts/TitleEditing.vue';

const route = useRoute();
const designStore = useDesignStore();
const sessionId = computed(() => route.params?.id);
const isCollapse = computed(() => designStore.isCollapse);
const sessionStore = useSessionStore();

// 定义 Ctrl+K 的处理函数
function handleCtrlK(event: KeyboardEvent) {
  event.preventDefault(); // 防止默认行为
  sessionStore.createSessionBtn();
}

// 设置全局的键盘按键监听
onKeyStroke(event => event.ctrlKey && event.key.toLowerCase() === 'k', handleCtrlK, {
  passive: false,
});

</script>

<template>
  <div class="chat-container">
    <TitleEditing />
    <div class="chat-content" :class="{ 'sidebar-collapsed': isCollapse }">
      <!-- 默认聊天页面 -->
      <ChatDefaul v-if="!sessionId" />
      <!-- 带id的聊天页面 -->
      <ChatWithId v-else />
    </div>
  </div>
</template>

<style lang="scss" scoped>
.chat-container {
  position: relative;
  display: flex;
  width: 100%;
  height: 100%;
  overflow-anchor: none;
}

.chat-content {
  flex: 1;
  display: flex;
  flex-direction: column;
  align-items: center;
  //padding-left: var(--sidebar-default-width, 280px);
  transition: padding-left 0.3s ease;
  box-sizing: border-box;
}

.chat-content.sidebar-collapsed {
  padding-left: 0;
}
</style>
