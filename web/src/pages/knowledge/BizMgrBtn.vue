<script lang="ts" setup>
import type { BizSpaceVO } from '@/api/knowledge/types'
import { addBizSpace, deleteBizSpace, updateBizSpace } from '@/api/knowledge'
/**
 * 列表
 */
const listDrawer = ref(false)
const editDrawer = ref(false)

/**
 * 业务空间列表、文件空间列表, 数据对象在父组件，子组件事件通知
 */
const props = defineProps<{ bizSpaces: BizSpaceVO[]}>()
const emit = defineEmits(['bizSpacesRefresh', 'refreshFileList'])
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
  id: 0,
  name: '',
  collection: '',
  desc: '',
})

/**
 * 打开编辑抽屉
 * @param row 业务空间数据，为空或 undefined 时视为新建
 */
const openEditDrawer = (row?: BizSpaceVO) => {
  resetForm()
  if (row) {
    // 编辑模式：用 row 数据填充表单
    form.name = row.name
    form.collection = row.collection
    form.desc = row.desc
    form.id = row.id
    editDrawer.value = true
  } else {
    // 新建模式：直接打开新建抽屉
    editDrawer.value = true
  }
}

const onEditDrawerSubmit = async () => {
  try {
    if (form.id === 0) {
      // 新建业务空间
      await addBizSpace(form)
    } else {
      // 更新业务空间
      await updateBizSpace(form)
    }
    editDrawer.value = false
    ElMessage.success('操作成功');
    // 刷新父组件的全局业务空间列表
    emit('bizSpacesRefresh')
    resetForm()
  } catch (error) {
    console.error('请求错误:', error);
    ElMessage.error('创建失败');
  }
}

// 清空表单
const resetForm = () => {
  form.name = ''
  form.collection = ''
  form.desc = ''
  form.id = 0
}


// 删除业务空间
const handleDelete = async (id: number) => {
  try {
    // 显示确认框
    await ElMessageBox.confirm('！！！注意会删除空间内所有文件！！！确定要删除该业务空间吗？', '操作确认', {
      confirmButtonText: '确认',
      cancelButtonText: '取消',
      type: 'error'
    })
    // 调用API执行删除
    const rspBody = await deleteBizSpace(id)
    
    if (rspBody.code === 200000) {
      ElMessage.success(rspBody.msg || '业务空间删除成功')
      // 删除成功后刷新全局空间列表、全局文件列表
      emit('bizSpacesRefresh')
      emit('refreshFileList')
    } else {
      ElMessage.error(rspBody.msg || '业务空间删除失败')
    }
  } catch (error: any) {
    // 如果用户取消操作，不显示错误消息
    if (error.name !== 'Cancel' && error !== 'cancel' && error?.action !== 'cancel') {
      console.error('业务空间删除出错:', error)
      ElMessage.error('操作失败，请稍后重试')
    }
  }
}

</script>

<template>
  <el-button type="primary" @click="listDrawer = true" style="margin-left: 5px;">业务空间管理</el-button>

  <!-- 列表抽屉 -->
  <el-drawer v-model="listDrawer" :direction="'rtl'" title="业务空间管理">
    <el-button size="small" type="primary" @click="editDrawer = true">
      新建
    </el-button>
    <el-table :data="props.bizSpaces" style="width: 100%" cell-class-name="word-break-cell">
      <!-- 修复列名和字段映射，使其与BizSpaceVO结构匹配 -->
      <el-table-column prop="name" label="业务名" width="100" />
      <el-table-column prop="collection" label="向量库集合" width="100" />
      <el-table-column prop="desc" label="业务描述" width="130"/>
      <el-table-column label="操作" width="160">
        <template #default="{ row }">
          <el-button size="small" @click="openEditDrawer(row)">
            编辑
          </el-button>
          <el-button size="small" type="danger" @click="handleDelete(row.id!)">
            删除
          </el-button>
        </template>
      </el-table-column>
    </el-table>
  </el-drawer>

  <!-- 编辑抽屉 -->
  <el-drawer v-model="editDrawer" title="编辑业务空间" :append-to-body="true" :before-close="handleClose">
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
        <el-button type="primary" @click="onEditDrawerSubmit">保存</el-button>
        <el-button @click="editDrawer = false">取消</el-button>
      </el-form-item>
    </el-form>
  </el-drawer>
</template>



  <!-- 样式 -->
  <style rel="stylesheet/scss" scoped lang="scss">
    :deep(.word-break-cell) {
      word-break: break-all;
      white-space: normal;
      height: auto;
      padding: 10px;
      line-height: 1.4;
    }
    
    /* 操作列保持不换行 */
    :deep(.el-table__column--fixed-right .word-break-cell) {
      white-space: nowrap;
    }
  </style>