<!-- Header 头部 -->
<script setup lang="ts">
import { useUserStore } from '@/stores';
import Logo from '@/layouts/components/Logo/index.vue';
import Avatar from './components/Avatar.vue';
import Menu from './components/Menu.vue';
import LoginBtn from './components/LoginBtn.vue';

const userStore = useUserStore();

</script>

<template>
  <div class="header-container">
    <div class="header-box relative z-10 top-0 left-0 right-0">
      <div class="absolute left-0 right-0 top-0 bottom-0 flex items-center flex-row">
        <div
          class="overflow-hidden flex h-full items-center flex-row flex-1 w-fit flex-shrink-0 min-w-0"
        >
          <div class="w-full flex items-center flex-row">
            <!-- Logo -->
            <div class="logo-wrapper pl-12px">
              <Logo />
            </div>

            <!-- 中间 -->
            <div class="middle-box flex-1 min-w-0 ml-12px">
            </div>
          </div>
        </div>

        <!-- 右边 -->
        <div class="right-box flex h-full items-center pr-20px flex-shrink-0 mr-auto flex-row">
         <Menu />
          <Avatar v-show="userStore.token" />
          <LoginBtn v-show="!userStore.token" />
        </div>
      </div>
    </div>
  </div>
</template>

<style scoped lang="scss">
.header-container {
  display: flex;
  flex-shrink: 0;
  flex-direction: column;
  width: 100%;
  height: fit-content;
  .header-box {
    width: 100%;
    height: var(--header-container-default-heigth);
    margin: 0 var(--sidebar-right-container-default-width, 0) 0 0;
  }
}

.logo-wrapper {
  display: flex;
  align-items: center;
  height: 100%;
}
</style>
