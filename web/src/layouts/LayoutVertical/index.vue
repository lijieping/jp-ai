<!-- 纵向布局作为基础布局 -->
<script setup lang="ts">
import { computed } from 'vue';
import { useRoute } from 'vue-router';
import Header from '@/layouts/components/Header/index.vue';
import Changelog from '@/layouts/components/Changelog/index.vue';
import Main from '@/layouts/components/Main/index.vue';
import { defineAsyncComponent } from 'vue'
import { useDesignStore } from '@/stores';
import { SIDE_BAR_WIDTH } from '@/config/index';

const designStore = useDesignStore()
const isCollapse = computed(() => designStore.isCollapse)
const route = useRoute();
const biz_module = computed(() => route.matched[1]?.name);

onMounted(() => {
  // 全局设置侧边栏默认宽度 (这个是不变的，一开始就设置)
  document.documentElement.style.setProperty(`--sidebar-default-width`, `${SIDE_BAR_WIDTH}px`);
  if (designStore.isCollapse) {
    document.documentElement.style.setProperty(`--sidebar-left-container-default-width`, ``);
  }
  else {
    document.documentElement.style.setProperty(
      `--sidebar-left-container-default-width`,
      `${SIDE_BAR_WIDTH}px`,
    );
  }
});

/* 预留侧边栏，各个模块自己实现” */
const sidebarComponent = computed(() => {
  const loader = route.meta?.sidebarComponent as (() => Promise<any>) | undefined
  return loader ? defineAsyncComponent(loader) : null
})

</script>

<template>

  <el-container class="layout-container" v-if="biz_module === 'chat-module'">
    <!-- 聊天模式布局 -->
    <el-aside :class="isCollapse ? 'layout-aside-collapsed' : 'layout-aside'">
      <component :is="sidebarComponent" />
    </el-aside>
    <el-container>
    <el-header class="layout-header">
      <Header />
    </el-header>
    <el-main>
      <Main />
      <Changelog />
    </el-main>
    </el-container>
  </el-container>

  <el-container v-else class="layout-container">
    <!-- header + content布局 -->
    <el-header class="layout-header">
      <Header />
    </el-header>
    <el-container>
      <el-main>
        <Main />
      </el-main>
    </el-container>
  </el-container>
</template>

<style lang="scss" scoped>
.layout-container {
  position: relative;
  width: 100%;
  height: 100vh;
  overflow: hidden;

  .layout-header {
    padding: 0;
  }

  .layout-main {
    height: 100%;
    padding: 0;
  }

  display: flex;
}

.layout-aside {
  width: var(--sidebar-default-width);
}

.layout-aside-collapsed {
  width: 40px
}
</style>
