<script setup lang="ts">
interface ChangelogItem {
  date: string;
  content: string[];
}

const visible = ref(true);

const changelogData = ref<ChangelogItem[]>([
  {
    date: '2025-12-20',
    content: [
      '演示视频',
    ]
  },
]);

// 只展示最近3条
const recentChangelog = computed(() => changelogData.value.slice(0, 3));

const handleClose = () => {
  visible.value = false;
};
</script>

<template>
  <el-card 
    v-if="visible"
    class="changelog-card" 
    shadow="hover"
    :body-style="{ padding: '16px' }"
  >
    <!-- <div class="video-link">
      <a href="https://example.com/demo-video" target="_blank" class="demo-video-link">
        <el-icon><VideoPlay /></el-icon>
        <span>观看演示视频</span>
      </a>
    </div> -->
    <div class="card-header">
      <span>更新日志</span>
      <el-icon class="close-icon" @click="handleClose">
        <Close />
      </el-icon>
    </div>
    <div class="changelog-content">
      <div v-for="(item, index) in recentChangelog" :key="index" class="changelog-item">
        <div class="changelog-date">{{ item.date }}</div>
        <ul class="changelog-list">
          <li v-for="(text, idx) in item.content" :key="idx">{{ text }}</li>
        </ul>
      </div>
    </div>
  </el-card>
</template>

<style scoped lang="scss">
.changelog-card {
  position: fixed;
  right: 20px;
  top: 76px; // Header 高度 56px + 间距 20px
  width: 200px;
  max-height: 400px;
  overflow-y: auto;
  z-index: 999;
  pointer-events: auto;
  background: linear-gradient(135deg, rgba(102, 126, 234, 0.75) 0%, rgba(118, 75, 162, 0.85) 100%);
  color: #ffffff;
  border: none;
  backdrop-filter: blur(10px);
  
  :deep(.el-card__body) {
    background: transparent;
  }
  
  .card-header {
    display: flex;
    justify-content: space-between;
    align-items: center;
    margin-bottom: 12px;
    font-weight: 600;
    color: #ffffff;
    
    .close-icon {
      cursor: pointer;
      font-size: 18px;
      color: #ffffff;
      
      &:hover {
        color: rgba(255, 255, 255, 0.7);
      }
    }
  }
  
  .video-link {
    margin-bottom: 12px;
    padding-bottom: 12px;
    border-bottom: 1px solid rgba(255, 255, 255, 0.2);
    
    .demo-video-link {
      display: inline-flex;
      align-items: center;
      gap: 8px;
      padding: 8px 12px;
      background: rgba(255, 255, 255, 0.95);
      color: #667eea;
      text-decoration: none;
      font-size: 14px;
      font-weight: 600;
      border-radius: 6px;
      transition: all 0.3s;
      box-shadow: 0 2px 8px rgba(0, 0, 0, 0.15);
      
      &:hover {
        background: #ffffff;
        transform: translateY(-2px);
        box-shadow: 0 4px 12px rgba(0, 0, 0, 0.2);
        
        .el-icon {
          transform: scale(1.15);
        }
      }
      
      .el-icon {
        font-size: 18px;
        transition: transform 0.3s;
        color: #667eea;
      }
    }
  }
  
  .changelog-content {
    font-size: 14px;
    line-height: 1.6;
    
    .changelog-item {
      margin-bottom: 16px;
      
      &:last-child {
        margin-bottom: 0;
      }
      
      .changelog-date {
        font-weight: 600;
        color: #ffffff;
        margin-bottom: 8px;
        font-size: 13px;
        opacity: 0.95;
      }
      
      .changelog-list {
        margin: 0;
        padding-left: 20px;
        
        li {
          margin-bottom: 4px;
          color: rgba(255, 255, 255, 0.9);
          
          &:last-child {
            margin-bottom: 0;
          }
        }
      }
    }
  }
}
</style>
