<script lang="ts" setup>
import { layoutRouter } from '@/routers/modules/staticRouter'
// 过滤出要显示的菜单
const menuRouteRecords = layoutRouter.filter(r =>  r.children && r.children.length > 0)
                                  .map(r => r.children!.filter(c => c.meta && (c.meta as any).nameInMenu))
                                  .flat();

</script>

<template>
  <el-menu
    router
    mode="horizontal"
    :ellipsis="false"
    :default-active="$route.path"
  >
    <template v-for="r in menuRouteRecords" :key="r.path">
      <el-menu-item :index="'/' + r.path">
        <el-icon v-if="(r.meta as any)?.icon">
            <component :is="(r.meta as any).icon" />
        </el-icon>
        <span>
            {{ (r.meta as any)?.nameInMenu }}
        </span>
      </el-menu-item>
    </template>
  </el-menu>
</template>

<style scoped>
.el-menu--horizontal > .el-menu-item:nth-child(1) {
  margin-right: auto;
}
</style>
