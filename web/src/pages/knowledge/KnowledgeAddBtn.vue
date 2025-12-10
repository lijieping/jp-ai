<script lang="ts" setup>
import { listAllBizSpaces, uploadFilesToBizSpace, getSupportedFileTypes } from '@/api/knowledge'
import { onMounted, ref, defineEmits } from 'vue'
import type { BizSpaceVO } from '@/api/knowledge/types'
import { ElMessageBox, ElMessage } from 'element-plus'
import { UploadFilled, QuestionFilled } from '@element-plus/icons-vue'

/**
 * 文件上传抽屉相关
 */
const drawer = ref(false)

// 业务空间相关数据
const bizSpaces = ref<BizSpaceVO[]>([])
const selectedSpaceId = ref<number>(0) // 提供默认值0，避免undefined问题

// 上传文件相关，使用any类型暂时绕过类型检查
const fileList = ref<any[]>([])
const uploadRef = ref()
const description = ref('') // 添加描述字段
// 新的文件类型接口返回格式类型定义
interface FileTypeCategory {
  name: string;
  exts: string[];
}

const supportedFileTypes = ref<Record<string, FileTypeCategory>>({}) // 修改为对象类型
const uploadTip = ref<string>('加载中...') // 上传提示语

// 加载业务空间列表
const loadBizSpaces = async () => {
    try {
        const res = await listAllBizSpaces()
        bizSpaces.value = res.data || []
        // 如果有业务空间，默认选择第一个
        if (bizSpaces.value.length > 0) {
            selectedSpaceId.value = bizSpaces.value[0].id || 0 // 使用默认值0，避免undefined问题
        }
    } catch (error) {
        console.error('获取业务空间列表失败:', error)
        ElMessage.error('获取业务空间列表失败')
    }
}

const handleClose = (done: () => void) => {
    ElMessageBox.confirm('将失去已填写内容，确定退出吗？')
        .then(() => {
            // 清空文件列表和描述
            fileList.value = []
            description.value = '' // 清空描述
            done()
        })
        .catch(() => {
            // catch error
        })
}

// 文件状态改变时(添加、上传成功、上传失败)的钩子
const handleChange = (file: any, fileListParam: any) => {
    // 校验文件类型
    console.log('文件状态改变:', file.name, file.status)
    const isValidType = validateFileType(file.name)
    console.log('准备上传文件:', file.name, "类型有效:", isValidType)
    console.log('当前文件列表:', fileListParam)
    if (!isValidType) {
        ElMessage.error(`不支持的文件类型: ${file.name}。`)
        // 从文件列表中移除该文件
        const index = fileListParam.indexOf(file)
        if (index > -1) {
            fileListParam.splice(index, 1)
        }
    }
    // 更新文件列表
    fileList.value = fileListParam
    console.log('更新后文件列表:', fileListParam)
}

// 定义自定义事件
const emit = defineEmits<{
    'file-uploaded': []
}>()

// 提交表单
async function onSubmit() {
    // 检查是否选择了业务空间
    if (!selectedSpaceId.value) {
        ElMessage.warning('请选择业务空间')
        return
    }

    // 检查是否选择了文件
    if (fileList.value.length === 0) {
        ElMessage.warning('请选择要上传的文件')
        return
    }
    console.log('上传文件:', fileList.value, 'selectedSpaceId:', selectedSpaceId.value)

    try {
        // 提取raw文件对象
        const files = fileList.value.map(file => file.raw!).filter(Boolean)

        // 使用api函数上传文件，传递描述字段
        await uploadFilesToBizSpace(selectedSpaceId.value, files, description.value)

        ElMessage.success('文件上传成功')
        // 触发文件上传成功事件，通知父组件刷新表格
        emit('file-uploaded')
        drawer.value = false
        // 清空文件列表和描述
        fileList.value = []
        description.value = '' // 清空描述
    } catch (error) {
        console.error('文件上传失败:', error)
        ElMessage.error('文件上传失败')
    }
}

// 验证文件类型是否支持
const validateFileType = (fileName: string): boolean => {
    console.log('验证文件类型:', fileName, '支持的类型:', supportedFileTypes.value)
    if (!Object.keys(supportedFileTypes.value).length) {
        // 如果支持的文件类型列表为空，暂时允许上传（可以选择阻止或允许，这里选择允许）
        return true
    }

    // 获取文件扩展名（包含点）
    const fileExtension = fileName.substring(fileName.lastIndexOf('.')).toLowerCase()
    console.log('文件扩展名:', fileExtension)
    
    // 检查扩展名是否在支持的类型列表中
    for (const category of Object.values(supportedFileTypes.value)) {
        if (category.exts.includes(fileExtension)) {
            return true
        }
    }
    return false
}

// 获取支持的文件类型
const loadSupportedFileTypes = async () => {
    try {
        const res = await getSupportedFileTypes()
        supportedFileTypes.value = res.data || {} // 确保赋值为对象类型
        // 根据获取到的文件类型对象生成提示语 (此提示语现在仅用于文件上传错误提示)
        uploadTip.value = Object.keys(supportedFileTypes.value).length > 0
            ? `不支持的文件类型`
            : '获取文件类型失败'
    } catch (error) {
        console.error('获取支持的文件类型失败:', error)
        uploadTip.value = '获取支持的文件类型失败，请稍后重试'
    }
}

// 组件挂载时加载业务空间列表和支持的文件类型
onMounted(() => {
    loadBizSpaces()
    loadSupportedFileTypes()
})
</script>

<template>
    <el-button type="primary" @click="drawer = true">上传知识</el-button>

    <el-drawer v-model="drawer" :direction="'rtl'" :before-close="handleClose">
        <el-form label-width="auto" style="max-width: 600px">
            <el-form-item label="业务空间">
                <el-select v-model="selectedSpaceId" placeholder="请选择业务空间" style="width: 240px" filterable>
                    <el-option v-for="space in bizSpaces" :key="space.id || space.name" :label="space.name" :value="space.id || 0" />
                </el-select>
            </el-form-item>

            <el-form-item label="文件描述">
                <el-input v-model="description" type="textarea" placeholder="请输入文件描述（可选）" :rows="3"
                    style="width: 100%;" />
            </el-form-item>

            <el-form-item label="文件">
                <el-upload ref="uploadRef" v-model:file-list="fileList" class="upload-demo" drag multiple action=""
                    :auto-upload="false" :on-change="handleChange">
                    <el-icon class="el-icon--upload"><upload-filled /></el-icon>
                    <div class="el-upload__text">
                        Drop file here or <em>click to upload</em>
                    </div>
                    <template #tip>
                        <div class="el-upload__tip">
                            
                            rag支持的文件类型
                            <el-popover
                                placement="top"
                                width="400"
                                trigger="hover"
                            >
                                <template #reference>
                                    <el-icon class="tip-icon" size="middle">
                                        <QuestionFilled />
                                    </el-icon>
                                </template>
                                <div v-if="Object.keys(supportedFileTypes).length > 0">
                                    <div v-for="(category, key) in supportedFileTypes" :key="key">
                                        {{ category.name }}：{{ category.exts.join(',') }}
                                    </div>
                                </div>
                                <div v-else>暂不可用</div>
                            </el-popover>
                        </div>
                    </template>
                </el-upload>
            </el-form-item>

            <el-form-item>
                <el-button type="primary" @click="onSubmit">上传</el-button>
                <el-button @click="drawer = false">取消</el-button>
            </el-form-item>
        </el-form>
    </el-drawer>
</template>

<style scoped></style>