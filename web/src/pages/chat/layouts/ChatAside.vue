<!-- Aside 侧边栏 -->
<script setup lang="ts">
import type { ConversationItem } from 'vue-element-plus-x/types/Conversations';
import type { ChatSessionVo } from '@/api/session/types';
import { useRoute, useRouter } from 'vue-router';
import { get_session, generate_session_title } from '@/api';
import SvgIcon from '@/components/SvgIcon/index.vue';
import Collapse from '@/pages/chat/layouts/Collapse.vue';
import { useDesignStore } from '@/stores';
import { useSessionStore } from '@/stores/modules/session';
import { useWindowWidthObserver } from '@/hooks/useWindowWidthObserver';


const route = useRoute();
const router = useRouter();
const designStore = useDesignStore();
const sessionStore = useSessionStore();

const sessionId = computed(() => route.params?.id);
const conversationsList = computed(() => sessionStore.sessionList);
const loadMoreLoading = computed(() => sessionStore.isLoadingMore);
const active = ref<string | undefined>();

useWindowWidthObserver();

onMounted(async () => {
  // 获取会话列表
  await sessionStore.requestSessionList();
  // 高亮最新会话
  if (conversationsList.value.length > 0 && sessionId.value) {
    const currentSessionRes = await get_session(`${sessionId.value}`);
    // 通过 ID 查询详情，设置当前会话 (因为有分页)
    sessionStore.setCurrentSession(currentSessionRes.data);
  }
});

watch(
  () => sessionStore.currentSession,
  (newValue) => {
    active.value = newValue ? `${newValue.conv_id}` : undefined;
  },
);

// 监听是否需要生成标题
watch(
  () => sessionStore.shouldGenerateTitle,
  async (newValue) => {
    if (newValue) {
      try {
        // 获取当前sessionId
        const sessionId = route.params?.id;
        // 检查sessionId是否有效
        if (sessionId && sessionId !== 'not_login') {
          // 调用生成标题的接口
          const res = await generate_session_title(`${sessionId}`);
          // 获取标题字符串
          const title = res.data;
          // 找到对应会话并更新标题
          if (title && typeof title === 'string') {
            // 更新会话列表中的标题
            const sessionIndex = sessionStore.sessionList.findIndex(item => item.conv_id === `${sessionId}`);
            if (sessionIndex !== -1) {
              sessionStore.sessionList[sessionIndex].title = title;
            }
            // 更新当前会话的标题
            if (sessionStore.currentSession && sessionStore.currentSession.conv_id === `${sessionId}`) {
              sessionStore.setCurrentSession({
                ...sessionStore.currentSession,
                title,
              });
            }
          }
        }
      } catch (error) {
        console.error('生成会话标题失败:', error);
      } finally {
        // 重置生成标题状态
        sessionStore.resetGenerateTitle();
      }
    }
  },
);

// 创建会话
function handleCreatChat() {
  // 创建会话, 跳转到默认聊天
  sessionStore.createSessionBtn();
}

// 切换会话
function handleChange(item: ConversationItem<ChatSessionVo>) {
  sessionStore.setCurrentSession(item);
  router.replace({
    name: 'chatWithId',
    params: {
      id: item.conv_id,
    },
  });
}

// 处理组件触发的加载更多事件
async function handleLoadMore() {
  if (!sessionStore.hasMore)
    return; // 无更多数据时不加载
  await sessionStore.loadMoreSessions();
}

// 右键菜单
function handleMenuCommand(command: string, item: ConversationItem<ChatSessionVo>) {
  switch (command) {
    case 'delete':
      ElMessageBox.confirm('删除后，聊天记录将不可恢复。', '确定删除对话？', {
        confirmButtonText: '确定',
        cancelButtonText: '取消',
        type: 'warning',
        confirmButtonClass: 'el-button--danger',
        cancelButtonClass: 'el-button--info',
        roundButton: true,
        autofocus: false,
      })
        .then(() => {
          // 删除会话
          sessionStore.deleteSessions([item.conv_id!]);
          nextTick(() => {
            if (item.conv_id === active.value) {
              // 如果删除当前会话 返回到默认页
              sessionStore.createSessionBtn();
            }
          });
        })
        .catch(() => {
          // 取消删除
        });
      break;
    case 'rename':
      ElMessageBox.prompt('', '编辑对话名称', {
        confirmButtonText: '确定',
        cancelButtonText: '取消',
        inputErrorMessage: '请输入对话名称',
        confirmButtonClass: 'el-button--primary',
        cancelButtonClass: 'el-button--info',
        roundButton: true,
        inputValue: item.title, // 设置默认值
        autofocus: false,
        inputValidator: (value) => {
          if (!value) {
            return false;
          }
          return true;
        },
      }).then(({ value }) => {
        sessionStore
          .updateSession({
            conv_id: item.conv_id!,
            title: value,
            user_id: item.user_id,
          })
          .then(() => {
            ElMessage({
              type: 'success',
              message: '修改成功',
            });
            nextTick(() => {
              // 如果是当前会话，则更新当前选中会话信息
              if (sessionStore.currentSession?.conv_id === item.conv_id) {
                sessionStore.setCurrentSession({
                  ...item,
                  title: value,
                });
              }
            });
          });
      });
      break;
    default:
      break;
  }
}
</script>

<template>
  <div class="aside-container" 
      :class="{
        //'aside-container-suspended': designStore.isSafeAreaHover, // 当鼠标悬停在安全区域（左侧边缘）时，显示悬停的侧边栏
        'aside-container-collapse': designStore.isCollapse, // 当侧边栏折叠时，隐藏aside-body
        // 折叠且未激活悬停时添加 no-delay 类
        //'no-delay': designStore.isCollapse && !designStore.hasActivatedHover, // 当侧边栏折叠且未激活过悬停时添加，用于移除过渡动画延迟，使折叠/展开更直接
      }">


      <div class="aside-wrapper">
        <div class="aside-header" >
          <Collapse />
        </div>
        <div class="aside-body" :class="{
          'aside-body-collapse': designStore.isCollapse, // 当侧边栏折叠时，隐藏aside-body
        }">
          <div class="creat-chat-btn-wrapper">
            <div class="creat-chat-btn" @click="handleCreatChat">
              <el-icon class="add-icon">
                <Plus />
              </el-icon>
              <span class="creat-chat-text">新对话</span>
              <SvgIcon name="ctrl+k" size="37" />
            </div>
          </div>
        
          <div class="aside-content">
            <div v-if="conversationsList.length > 0" class="conversations-wrap overflow-hidden">
              <Conversations
              v-model:active="active"
              :items="conversationsList"
              :label-max-width="200"
              :show-tooltip="true"
              :tooltip-offset="60"
              show-built-in-menu
              groupable
              row-key="conv_id"
              label-key="title"
              tooltip-placement="right"
              :load-more="handleLoadMore"
              :load-more-loading="loadMoreLoading"
              :items-style="{
                marginLeft: '8px',
                userSelect: 'none',
                borderRadius: '10px',
                padding: '8px 12px',
              }"
              :items-active-style="{
                backgroundColor: '#fff',
                boxShadow: '0 1px 2px rgba(0, 0, 0, 0.05)',
                color: 'rgba(0, 0, 0, 0.85)',
              }"
              :items-hover-style="{
                backgroundColor: 'rgba(0, 0, 0, 0.04)',
              }"
              @menu-command="handleMenuCommand"
              @change="handleChange"
              />
            </div>
          
            <el-empty v-else class="h-full flex-center" description="暂无对话记录" />
          </div>
        </div>
      </div>
      
    </div>
</template>

<style scoped lang="scss">
// 基础样式
.aside-container {
  flex:1;
  position: absolute;
  top: 0;
  left: 0;
  z-index: 10;
  width: var(--sidebar-default-width);
  height: 100%;
  pointer-events: auto;
  background-color: var(--sidebar-background-color);
  border-right: 0.5px solid var(--s-color-border-tertiary, rgb(0 0 0 / 8%));

  .aside-wrapper {
    display: flex;
    flex-direction: column;
    height: 100%;

    // 侧边栏头部样式
    .aside-header {
        display: flex;
        align-items: center;
        height: 36px;
        width: 36px;
        margin: 10px 12px 0;
        visibility: visible;
    }

    // 侧边栏内容样式
    .aside-body {
      .creat-chat-btn-wrapper {
        padding: 0 12px;
        .creat-chat-btn {
          display: flex;
          gap: 6px;
          align-items: center;
          padding: 8px 6px;
          margin-top: 16px;
          margin-bottom: 6px;
          color: #0057ff;
          cursor: pointer;
          user-select: none;
          background-color: rgb(0 87 255 / 6%);
          border: 1px solid rgb(0 102 255 / 15%);
          border-radius: 12px;
          &:hover {
            background-color: rgb(0 87 255 / 12%);
          }
          .creat-chat-text {
            font-size: 14px;
            font-weight: 700;
            line-height: 22px;
          }
          .add-icon {
            width: 24px;
            height: 24px;
            font-size: 16px;
          }
          .svg-icon {
            height: 24px;
            margin-left: auto;
            color: rgb(0 87 255 / 30%);
          }
        }
        
        .creat-chat-btn-collapse {
          display: flex;
          justify-content: center;
          align-items: center;
          width: 40px;
          height: 40px;
          margin: 8px auto;
          border-radius: 50%;
          background-color: var(--bg-primary, #ffffff);
          border: 1px solid var(--border-color, #e4e7ed);
          cursor: pointer;
          &:hover {
            background-color: var(--hover-color, #f5f7fa);
          }
        }
      }
      .aside-content {
        display: flex;
        flex: 1;
        flex-direction: column;
        height: 100%;
        min-height: 0;

        // 会话列表高度-基础样式
        .conversations-wrap {
          height: calc(100% - 70px);
          .label {
            display: flex;
            align-items: center;
            height: 100%;
          }
        }
      }
    }
  }
}

// 折叠样式
.aside-body-collapse {

  /* 禁用悬停事件 */
  pointer-events: none;
  border: 1px solid rgb(0 0 0 / 8%); // 1 px 的浅灰色描边。
  border-radius: 15px; // 圆角 15 px
  box-shadow: //两层阴影：外层长的做“浮起”效果，内层 1 px 做细微边框。
    0 10px 20px 0 rgb(0 0 0 / 10%),
    0 0 1px 0 rgb(0 0 0 / 15%);

  // 透明且向左偏移
  width: 0;
  opacity: 0;                 // 完全透明
  transform: translateX(-100%); // 整体向左平移一个自身宽度，跑出可视区
  // transition: opacity 0.3s ease 0.3s, transform 0.3s ease 0.3s; //给透明度和位移都加 0.3 s 过渡，且统一延迟 0.3 s 执行。
}

// 折叠样式
.aside-container-collapse {
  width: 40px;                           // 只保留头部按钮宽度
  border-right: none;                    // 可选：让线条消失
}

// 样式穿透
:deep() {
  // 会话列表背景色
  .conversations-list {
    background-color: transparent !important;
  }

  // 群组标题样式 和 侧边栏菜单背景色一致
  .conversation-group-title {
    padding-left: 12px !important;
    background-color: var(--sidebar-background-color) !important;
  }
}
</style>
