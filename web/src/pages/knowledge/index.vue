<!-- 知识库页面 -->
<script setup lang="ts">
import BizMgrBtn from '@/pages/knowledge/BizMgrBtn.vue'
import KnowledgeAddBtn from '@/pages/knowledge/KnowledgeAddBtn.vue'
import { listAllBizSpaces, getKnowledgeFileList, deleteKnowledgeFile } from '@/api/knowledge'
import type { BizSpaceVO, KnowledgeFileVO, KnowledgeFileParams } from '@/api/knowledge/types'
import { ElMessage, ElMessageBox } from 'element-plus'
import { onMounted, reactive, ref } from 'vue'

// 组件大小类型
type ComponentSize = 'large' | 'default' | 'small'

// =========================================================================
// 响应式数据定义
// =========================================================================

// 表单数据
const formInline = reactive({
  user: '',
})

// 业务空间选择相关数据
const bizSpaces = ref<BizSpaceVO[]>([])
const selectedSpaceId = ref<number>(0)

// 表格数据相关
const tableData = ref<KnowledgeFileVO[]>([])
const tableLoading = ref(false)

// 分页相关数据
const currentPage = ref(1)
const pageSize = ref(20)
const total = ref(0)
const size = ref<ComponentSize>('default')
const background = ref(false)
const disabled = ref(false)

// =========================================================================
// 业务逻辑函数
// =========================================================================

// 加载业务空间列表
const loadBizSpaces = async () => {
  try {
    const res = await listAllBizSpaces()
    bizSpaces.value = res.data || []
  } catch (error) {
    console.error('获取业务空间列表失败:', error)
    ElMessage.error('获取业务空间列表失败')
  }
}

// 加载知识库文件列表
const loadKnowledgeFiles = async () => {
  try {
    tableLoading.value = true

    // 构建查询参数
    const params: KnowledgeFileParams = {
      pageSize: pageSize.value,
      curPage: currentPage.value,
      spaceId: selectedSpaceId.value ?? 0 //0表示全部
    }

    const res = await getKnowledgeFileList(params)
    tableData.value = res.data?.list || []
    total.value = res.data?.total || 0
  } catch (error) {
    console.error('获取知识库文件列表失败:', error)
    ElMessage.error('获取知识库文件列表失败')
  } finally {
    tableLoading.value = false
  }
}

// =========================================================================
// 事件处理函数
// =========================================================================

// 分页大小变化处理
const handleSizeChange = (val: number) => {
  pageSize.value = val
  loadKnowledgeFiles()
}

// 页码变化处理
const handleCurrentChange = (val: number) => {
  currentPage.value = val
  loadKnowledgeFiles()
}

// 查询按钮点击事件
const handleQuery = () => {
  currentPage.value = 1
  loadKnowledgeFiles()
}

// 删除操作
const handleDelete = async (_: any, row: KnowledgeFileVO) => {
  try {
    // 显示确认框
    await ElMessageBox.confirm('确定要删除该文件吗？', '操作确认', {
      confirmButtonText: '确认',
      cancelButtonText: '取消',
      type: 'warning'
    })
    // 调用API执行文件删除
    const rspBody = await deleteKnowledgeFile(row.id!)
    
    if (rspBody.code === 200000) {
      ElMessage.success(rspBody.msg || '文件删除成功')
      // 删除成功后刷新表格数据
      loadKnowledgeFiles()
    } else {
      ElMessage.error(rspBody.msg || '文件删除失败')
    }
  } catch (error: any) {
    // 如果用户取消操作，不显示错误消息
    if (error.name !== 'Cancel') {
      if (error === 'cancel' || error?.action === 'cancel') {
        console.log('用户取消了文件删除操作')
      } else {
        console.error('文件删除出错:', error)
        ElMessage.error('操作失败，请稍后重试')
      }
    }
  }
}

// =========================================================================
// 生命周期钩子
// =========================================================================

// 组件挂载时执行
onMounted(() => {
  loadBizSpaces()
  loadKnowledgeFiles()
})
</script>

<template>

  <el-container style="height: 100%;">
    <el-header>
      <el-row>
        <el-col :span="18">
          <el-form :inline="true" :model="formInline" style="margin-bottom: -22px;">
            <el-form-item label="业务空间">
              <el-select v-model="selectedSpaceId" placeholder="请选择业务空间" style="width: 240px" clearable filterable>
                <el-option key="0" label="全部/请选择" :value="0" />
                <el-option v-for="space in bizSpaces" :key="space.id" :label="space.name" :value="space.id" />
              </el-select>
            </el-form-item>
            <el-form-item>
              <el-button type="primary" @click="handleQuery">查询</el-button>
            </el-form-item>
          </el-form>
        </el-col>
        <el-col :span="6" style="display: flex; justify-content: flex-end;">
           <!-- 在KnowledgeAddBtn组件上添加事件监听器 -->
          <KnowledgeAddBtn @refreshFileList="loadKnowledgeFiles" v-model:bizSpaces="bizSpaces"/>
          <BizMgrBtn v-model:bizSpaces="bizSpaces" @bizSpacesRefresh="loadBizSpaces" @refreshFileList="loadKnowledgeFiles"/>
        </el-col>
      </el-row>
    </el-header>

    <el-main>
      <el-table v-loading="tableLoading" :data="tableData" height="100%" style="width: 100%">
        <el-table-column prop="file_name" label="文件名" width="180" />
        <el-table-column prop="file_type" label="文件类型" width="100" />
        <el-table-column prop="file_size" label="文件大小" width="100">
          <template #default="{ row }">
            {{ (row.file_size / 1024).toFixed(2) }} KB
          </template>
        </el-table-column>
        <el-table-column prop="description" label="描述" min-width="170">
          <template #default="{ row }">
            {{ row.description || '-' }}
          </template>
        </el-table-column>
        <el-table-column prop="space_name" label="业务空间" width="150" />
        <el-table-column prop="user_name" label="上传用户" width="100" />
        <el-table-column prop="created_at" label="上传时间" width="180" />
        <el-table-column prop="status" label="文件状态" width="100">
          <template #default="{ row }">
            <el-tag :type="row.status === 1 ? 'success' : 'danger'">
              {{ row.status === 1 ? '有效' : '失效' }}
            </el-tag>
          </template>
        </el-table-column>
        <el-table-column prop="rag_status" label="RAG处理状态" width="120">
          <template #default="{ row }">
            <el-tooltip 
              v-if="row.rag_status === 3 && row.msg"
              :content="row.msg" 
              placement="top"
              effect="dark"
            >
              <el-tag :type="row.rag_status === 0 ? 'warning': row.rag_status === 1 ? 'warning' : row.rag_status === 2 ? 'success' : 'danger'">
                {{ row.rag_status === 0 ? '待执行': row.rag_status === 1 ? '执行中' : row.rag_status === 2 ? '成功' : '失败' }}
              </el-tag>
            </el-tooltip>
            <el-tag 
              v-else
              :type="row.rag_status === 0 ? 'warning': row.rag_status === 1 ? 'warning' : row.rag_status === 2 ? 'success' : 'danger'"
            >
              {{ row.rag_status === 0 ? '待执行': row.rag_status === 1 ? '执行中' : row.rag_status === 2 ? '成功' : '失败' }}
            </el-tag>
          </template>
        </el-table-column>
        <el-table-column label="操作" width="240">
          <template #default="{ row, $index }">
            <el-button size="small" type="danger" @click="handleDelete($index, row)">
              删除
            </el-button>
          </template>
        </el-table-column>
      </el-table>

    </el-main>

    <el-footer>
      <el-pagination v-model:current-page="currentPage" v-model:page-size="pageSize" :size="size" :disabled="disabled"
        :background="background" layout="prev, pager, next, jumper, ->, total, sizes" :total="total"
        @size-change="handleSizeChange" @current-change="handleCurrentChange" />
    </el-footer>
  </el-container>
</template>

<style scoped lang="scss"></style>