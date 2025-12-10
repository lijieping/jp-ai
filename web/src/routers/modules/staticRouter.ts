import type { RouteRecordRaw } from 'vue-router';
import { HOME_URL } from '@/config';

// LayoutRouter[布局路由]
export const layoutRouter: RouteRecordRaw[] = [
  {
    path: '/',
    redirect: HOME_URL,        // 默认进聊天首页
    component: () => import('@/layouts/index.vue'),
    children: [
      /* ----------- 聊天模块 ----------- */
      {
        path: 'chat',
        name: 'chat-module',  // 模块节点，可以不要真实组件
        redirect: { name: 'chat' },
        meta: { nameInMenu: '智能助手', icon: 'HomeFilled' },
        children: [
          {
            path: '',         // 对应 /chat
            name: 'chat',
            component: () => import('@/pages/chat/index.vue'),
            meta: {
              sidebarComponent: () => import('@/pages/chat/layouts/ChatAside.vue'),
              isDefaultChat: true,
            },
          },
          {
            path: ':id',      // 对应 /chat/:id
            name: 'chatWithId',
            component: () => import('@/pages/chat/index.vue'),
            meta: {
              sidebarComponent: () => import('@/pages/chat/layouts/ChatAside.vue'),
              isDefaultChat: false,
            },
          },
        ],
      },

      /* ----------- 知识库模块 ----------- */
      {
        path: 'knowledge-base',
        name: 'kb-module',
        redirect: { name: 'knowledge-base' },
        meta: { nameInMenu: '知识库', icon: 'DocumentCopy' },
        children: [
          {
            path: '',         // 对应 /knowledge-base
            name: 'knowledge-base',
            component: () => import('@/pages/knowledge/index.vue'),
            meta: {
            },
          },
        ],
      },
    ],
  },
];

// staticRouter[静态路由] 预留
export const staticRouter: RouteRecordRaw[] = [];

// errorRouter (错误页面路由)
export const errorRouter = [
  {
    path: '/403',
    name: '403',
    component: () => import('@/pages/error/403.vue'),
    meta: {
      title: '403页面',
      enName: '403 Page', // 英文名称
      icon: 'QuestionFilled', // 菜单图标
      isHide: '1', // 代表路由在菜单中是否隐藏，是否隐藏[0隐藏，1显示]
      isLink: '1', // 是否外链[有值则是外链]
      isKeepAlive: '0', // 是否缓存路由数据[0是，1否]
      isFull: '1', // 是否缓存全屏[0是，1否]
      isAffix: '1', // 是否缓存固定路由[0是，1否]
    },
  },
  {
    path: '/404',
    name: '404',
    component: () => import('@/pages/error/404.vue'),
    meta: {
      title: '404页面',
      enName: '404 Page', // 英文名称
      icon: 'CircleCloseFilled', // 菜单图标
      isHide: '1', // 代表路由在菜单中是否隐藏，是否隐藏[0隐藏，1显示]
      isLink: '1', // 是否外链[有值则是外链]
      isKeepAlive: '0', // 是否缓存路由数据[0是，1否]
      isFull: '1', // 是否缓存全屏[0是，1否]
      isAffix: '1', // 是否缓存固定路由[0是，1否]
    },
  },
  // 找不到path将跳转404页面
  {
    path: '/:pathMatch(.*)*',
    component: () => import('@/pages/error/404.vue'),
  },
];
