<script setup lang="ts">
import logo from '@/assets/images/stars-star.svg';
</script>

<template>
  <el-image :src="logo" alt="logo" fit="cover" class="logo-img" />
  <span class="logo-text max-w-150px text-overflow">光之裂隙</span>

  <!-- <el-image :src="logo2" alt="logo" fit="cover" class="logo-img2" /> -->
</template>

<style scoped lang="scss">
.logo-img {
  box-sizing: border-box;
  width: 36px;
  height: 36px;
  padding: 4px;
  overflow: hidden;
  background: none;
  border-radius: 50%;
  img {
    display: flex;
    align-items: center;
    justify-content: center;
    width: 100%;
    height: 100%;
  }
}
.logo-text {
  font-size: 16px;
  font-weight: 700;
  color: rgb(0 0 0 / 85%);
  transform: skewX(-2deg);
}


.logo-img2 {
  box-sizing: border-box;
  width: 216px;
  height: 36px;
  padding: 4px;
  overflow: hidden;
  background: none;
  img {
    display: flex;
    align-items: center;
    justify-content: center;
    width: 100%;
    height: 100%;
  }
}

</style>
