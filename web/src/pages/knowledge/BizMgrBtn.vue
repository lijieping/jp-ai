<script lang="ts" setup>
import type { BizSpaceVO } from '@/api/knowledge/types'
import { addBizSpace, listAllBizSpaces } from '@/api/knowledge'
import { onMounted } from 'vue'
/**
 * 列表
 */
const listDrawer = ref(false)
const createDrawer = ref(false)

// 改为响应式数据并定义类型
const tableData = ref<BizSpaceVO[]>([])

// 加载业务空间列表
const loadBizSpaces = async () => {
  try {
    const res = await listAllBizSpaces()
    tableData.value = res.data || []
  } catch (error) {
    console.error('获取业务空间列表失败:', error)
    ElMessage.error('获取业务空间列表失败')
  }
}

/**
 * 业务空间
 */
const handleClose = (done: () => void) => {
  ElMessageBox.confirm('将失去已填写内容，确定退出吗？')
    .then(() => {
      done()
    })
    .catch(() => {
      // catch error
    })
}
const form = reactive<BizSpaceVO>({
  name: '',
  collection: '',
  desc: '',
})

const onCreateDrawerSubmit = async () => {
  try {
    await addBizSpace(form)
    createDrawer.value = false
    ElMessage.success('创建成功');
    // 刷新列表
    loadBizSpaces()
    // 重置表单
    form.name = ''
    form.collection = ''
    form.desc = ''
  } catch (error) {
    console.error('请求错误:', error);
    ElMessage.error('创建失败');
  }
}

// 组件挂载时加载数据
onMounted(() => {
  loadBizSpaces()
})

</script>

<template>
  <el-button type="primary" @click="listDrawer = true" style="margin-left: 5px;">业务空间管理</el-button>

  <!-- 列表抽屉 -->
  <el-drawer v-model="listDrawer" :direction="'rtl'" title="业务空间管理">
    <el-button size="small" type="primary" @click="createDrawer = true">
      新建
    </el-button>
    <el-table :data="tableData" style="width: 100%">
      <!-- 修复列名和字段映射，使其与BizSpaceVO结构匹配 -->
      <el-table-column prop="name" label="业务名" width="180" />
      <el-table-column prop="collection" label="向量库集合" width="180" />
      <el-table-column prop="desc" label="业务描述" show-overflow-tooltip />
      <el-table-column label="操作">
        <template #default>
          <el-button size="small" @click="">
            编辑
          </el-button>
          <!-- <el-button size="small" type="danger" @click="">
              Delete
            </el-button> -->
        </template>
      </el-table-column>
    </el-table>
  </el-drawer>

  <!-- 新建抽屉 -->
  <el-drawer v-model="createDrawer" title="新建业务空间" :append-to-body="true" :before-close="handleClose">
    <el-form :model="form" label-width="auto" style="max-width: 600px">
      <el-form-item label="业务名">
        <el-input v-model="form.name" />
      </el-form-item>
      <el-form-item label="向量库集合">
        <el-input v-model="form.collection" />
      </el-form-item>
      <el-form-item label="业务描述">
        <el-input v-model="form.desc" type="textarea" />
      </el-form-item>
      <el-form-item>
        <el-button type="primary" @click="onCreateDrawerSubmit">Create</el-button>
        <el-button @click="createDrawer = false">Cancel</el-button>
      </el-form-item>
    </el-form>
  </el-drawer>
</template>