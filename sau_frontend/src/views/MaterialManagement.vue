<template>
  <div class="material-management">
    <div class="page-header">
      <h1>素材管理</h1>
    </div>
    
    <div class="material-list-container">
      <div class="material-search">
        <div class="material-search__filters">
          <el-input
            v-model="searchKeyword"
            placeholder="输入文件名搜索"
            prefix-icon="Search"
            clearable
            @clear="handleSearch"
            @input="handleSearch"
          />
          <el-select
            v-model="selectedMaterialType"
            placeholder="筛选类型"
            @change="handleSearch"
          >
            <el-option
              v-for="option in materialTypeFilterOptions"
              :key="option.value"
              :label="option.label"
              :value="option.value"
            />
          </el-select>
          <el-select
            v-model="selectedMaterialSort"
            placeholder="排序方式"
            @change="handleSearch"
          >
            <el-option
              v-for="option in materialSortOptions"
              :key="option.value"
              :label="option.label"
              :value="option.value"
            />
          </el-select>
        </div>
        <div class="action-buttons">
          <el-button type="primary" @click="handleUploadMaterial">上传素材</el-button>
          <el-button type="info" @click="handleRefresh" :loading="false">
            <el-icon :class="{ 'is-loading': isRefreshing }"><Refresh /></el-icon>
            <span v-if="isRefreshing">刷新中</span>
          </el-button>
        </div>
      </div>
      
      <div v-if="materials.length > 0" class="material-list">
        <el-table :data="materials" style="width: 100%">
          <el-table-column prop="uuid" label="UUID" width="180" />
          <el-table-column prop="filename" label="文件名" width="300" />
          <el-table-column label="类型" width="110">
            <template #default="scope">
              <el-tag :type="getFileTypeTag(scope.row.filename)" effect="plain" size="small">
                {{ getFileType(scope.row.filename) }}
              </el-tag>
            </template>
          </el-table-column>
          <el-table-column prop="filesize" label="文件大小" width="120">
            <template #default="scope">
              {{ scope.row.filesize }} MB
            </template>
          </el-table-column>
          <el-table-column prop="upload_time" label="上传时间" width="180" />
          <el-table-column label="操作">
            <template #default="scope">
              <el-button size="small" @click="handlePreview(scope.row)">预览</el-button>
              <el-button size="small" type="danger" @click="handleDelete(scope.row)">删除</el-button>
            </template>
          </el-table-column>
        </el-table>
        <div class="material-pagination">
          <el-pagination
            background
            layout="total, sizes, prev, pager, next, jumper"
            :current-page="currentPage"
            :page-size="pageSize"
            :page-sizes="materialPageSizeOptions"
            :total="totalMaterials"
            @current-change="handlePageChange"
            @size-change="handlePageSizeChange"
          />
        </div>
      </div>
      
      <div v-else class="empty-data">
        <el-empty description="暂无素材数据" />
      </div>
    </div>
    
    <!-- 上传对话框 -->
    <el-dialog
      v-model="uploadDialogVisible"
      title="上传素材"
      width="40%"
      @close="handleUploadDialogClose"
    >
      <div class="upload-form">
        <el-form label-width="80px">
          <el-form-item label="文件名称:">
            <el-input
              v-model="customFilename"
              placeholder="选填 (仅单个文件时生效)"
              :disabled="customFilenameDisabled"
              clearable
            />
          </el-form-item>
          <el-form-item label="选择文件">
            <el-upload
              class="upload-demo"
              drag
              multiple
              :auto-upload="false"
              :on-change="handleFileChange"
              :on-remove="handleFileRemove"
              :file-list="fileList"
            >
              <el-icon class="el-icon--upload"><Upload /></el-icon>
              <div class="el-upload__text">
                将文件拖到此处，或<em>点击上传</em>
              </div>
              <template #tip>
                <div class="el-upload__tip">
                  支持视频与图片素材，可一次选择多个文件。
                  视频格式：{{ VIDEO_FILE_FORMAT_TEXT }}；图片格式：{{ IMAGE_FILE_FORMAT_TEXT }}
                </div>
              </template>
            </el-upload>
          </el-form-item>
          <el-form-item label="上传列表" v-if="fileList.length > 0">
            <div class="upload-file-list">
              <div v-for="file in fileList" :key="file.uid" class="upload-file-item">
                <span class="file-name">{{ file.name }}</span>
                <el-progress
                  :percentage="uploadProgress[file.uid]?.percentage || 0"
                  :text-inside="true"
                  :stroke-width="20"
                  style="width: 100%; margin-top: 5px;"
                >
                  <span>{{ uploadProgress[file.uid]?.speed || '' }}</span>
                </el-progress>
              </div>
            </div>
          </el-form-item>
        </el-form>
      </div>
      <template #footer>
        <div class="dialog-footer">
          <el-button @click="uploadDialogVisible = false">取消</el-button>
          <el-button type="primary" @click="submitUpload" :loading="isUploading">
            {{ isUploading ? '上传中' : '确认上传' }}
          </el-button>
        </div>
      </template>
    </el-dialog>
    
    <MaterialPreviewDialog
      v-model="previewDialogVisible"
      :material="currentMaterial"
    />
  </div>
</template>

<script setup>
import { ref, computed, onMounted, watch } from 'vue'
import { Refresh, Upload } from '@element-plus/icons-vue'
import { ElMessage, ElMessageBox } from 'element-plus'
import { materialApi } from '@/api/material'
import MaterialPreviewDialog from '@/components/MaterialPreviewDialog.vue'
import {
  MATERIAL_PAGE_SIZE_OPTIONS,
  MATERIAL_SORT_OPTIONS,
  MATERIAL_TYPE_FILTER_OPTIONS,
  buildMaterialListQueryParams
} from '@/composables/materialListQuery.js'
import { summarizeMaterialUploadResults } from '@/composables/materialUploadBatch.js'
import { useMaterialPreviewDialog } from '@/composables/useMaterialPreviewDialog.js'
import { useAppStore } from '@/stores/app'
import {
  IMAGE_FILE_FORMAT_TEXT,
  VIDEO_FILE_FORMAT_TEXT,
  getMaterialType,
  getMaterialTypeTag
} from '@/constants/materialFormats'

// 获取应用状态管理
const appStore = useAppStore()

// 搜索和状态控制
const materials = ref([])
const searchKeyword = ref('')
const selectedMaterialType = ref(MATERIAL_TYPE_FILTER_OPTIONS[0].value)
const selectedMaterialSort = ref(MATERIAL_SORT_OPTIONS[0].value)
const currentPage = ref(1)
const pageSize = ref(MATERIAL_PAGE_SIZE_OPTIONS[1])
const totalMaterials = ref(0)
const isRefreshing = ref(false)
const isUploading = ref(false)

/**
 * 素材筛选项直接暴露给模板，确保选项来源与过滤逻辑共用一套定义。
 */
const materialTypeFilterOptions = MATERIAL_TYPE_FILTER_OPTIONS

/**
 * 排序选项集中维护，后续如果增加“按名称”之类排序，不需要再分散改模板常量。
 */
const materialSortOptions = MATERIAL_SORT_OPTIONS

/**
 * 分页尺寸集中维护，避免模板硬编码导致前后端默认页长不一致。
 */
const materialPageSizeOptions = MATERIAL_PAGE_SIZE_OPTIONS

// 对话框控制
const uploadDialogVisible = ref(false)
const {
  previewDialogVisible,
  currentPreviewMaterial: currentMaterial,
  openMaterialPreview
} = useMaterialPreviewDialog()

// 文件上传
const fileList = ref([])
const customFilename = ref('')
const customFilenameDisabled = computed(() => fileList.value.length > 1)
const uploadProgress = ref({}); // { [uid]: { percentage: 0, speed: '' } }


watch(fileList, (newList) => {
  if (newList.length <= 1) {
    // If you want to clear the custom name when going back to single file, uncomment below
    // customFilename.value = ''
  }
});


// 获取素材列表
const fetchMaterials = async ({ showSuccess = false } = {}) => {
  isRefreshing.value = true
  try {
    const response = await materialApi.getMaterialPage(
      buildMaterialListQueryParams({
        currentPage: currentPage.value,
        pageSize: pageSize.value,
        searchKeyword: searchKeyword.value,
        selectedType: selectedMaterialType.value,
        selectedSort: selectedMaterialSort.value
      })
    )
    
    if (response.code === 200) {
      materials.value = response.data
      currentPage.value = response.pagination?.page ?? currentPage.value
      pageSize.value = response.pagination?.page_size ?? pageSize.value
      totalMaterials.value = response.pagination?.total ?? response.data.length
      // 素材管理页已改成分页拉取，原有全量缓存不再可信，这里主动失效避免其他页面误用旧数据。
      invalidateMaterialCache()
      if (showSuccess) {
        ElMessage.success('刷新成功')
      }
    } else {
      ElMessage.error('获取素材列表失败')
    }
  } catch (error) {
    console.error('获取素材列表出错:', error)
    ElMessage.error('获取素材列表失败')
  } finally {
    isRefreshing.value = false
  }
}

// 搜索处理
const handleSearch = () => {
  currentPage.value = 1
  fetchMaterials()
}

/**
 * 手动刷新沿用当前筛选条件和页码，只额外提示成功消息。
 */
const handleRefresh = () => {
  fetchMaterials({ showSuccess: true })
}

/**
 * 切页时只替换页码，其他查询条件保持不变。
 */
const handlePageChange = (page) => {
  currentPage.value = page
  fetchMaterials()
}

/**
 * 切换分页大小后回到第一页，避免旧页码超过新总页数时出现空页。
 */
const handlePageSizeChange = (size) => {
  pageSize.value = size
  currentPage.value = 1
  fetchMaterials()
}

/**
 * 其他页面仍依赖全量素材缓存，这里在素材变更后主动失效，确保后续进入时会重新拉取。
 */
const invalidateMaterialCache = () => {
  appStore.setMaterials([])
}

// 上传素材
const handleUploadMaterial = () => {
  // 清空变量
  fileList.value = []
  customFilename.value = ''
  uploadProgress.value = {};
  uploadDialogVisible.value = true
}

// 关闭上传对话框时清空变量
const handleUploadDialogClose = () => {
  fileList.value = []
  customFilename.value = ''
  uploadProgress.value = {};
}

// 文件选择变更
const handleFileChange = (file, uploadFileList) => {
  fileList.value = uploadFileList;
  const newProgress = {};
  for (const f of uploadFileList) {
    newProgress[f.uid] = { percentage: 0, speed: '' };
  }
  uploadProgress.value = newProgress;
}

const handleFileRemove = (file, uploadFileList) => {
  fileList.value = uploadFileList;
  const newProgress = { ...uploadProgress.value };
  delete newProgress[file.uid];
  uploadProgress.value = newProgress;
}

// 提交上传
const submitUpload = async () => {
  if (fileList.value.length === 0) {
    ElMessage.warning('请选择要上传的文件')
    return
  }
  
  isUploading.value = true
  const uploadResults = []
  
  for (const file of fileList.value) {
    try {
      // 确保文件对象存在
      if (!file || !file.raw) {
        ElMessage.warning(`文件 ${file.name} 对象无效，已跳过`)
        uploadResults.push({ status: 'failure' })
        continue
      }
      
      const formData = new FormData()
      formData.append('file', file.raw)
      
      // 只有当只有一个文件时，自定义文件名才生效
      if (fileList.value.length === 1 && customFilename.value.trim()) {
        formData.append('filename', customFilename.value.trim())
      }
      
      let lastLoaded = 0;
      let lastTime = Date.now();

      const response = await materialApi.uploadMaterial(formData, (progressEvent) => {
        const progressData = uploadProgress.value[file.uid];
        if (!progressData) return;

        const progress = Math.round((progressEvent.loaded * 100) / progressEvent.total)
        progressData.percentage = progress;

        const currentTime = Date.now();
        const timeDiff = (currentTime - lastTime) / 1000; // in seconds
        const loadedDiff = progressEvent.loaded - lastLoaded;

        if (timeDiff > 0.5) { // Update speed every 0.5 seconds
          const speed = loadedDiff / timeDiff; // bytes per second
          if (speed > 1024 * 1024) {
            progressData.speed = (speed / (1024 * 1024)).toFixed(2) + ' MB/s';
          } else {
            progressData.speed = (speed / 1024).toFixed(2) + ' KB/s';
          }
          lastLoaded = progressEvent.loaded;
          lastTime = currentTime;
        }
      })
      
      if (response.code === 200) {
        ElMessage.success(`文件 ${file.name} 上传成功`)
        const progressData = uploadProgress.value[file.uid];
        if(progressData) progressData.speed = '完成';
        uploadResults.push({ status: 'success' })
      } else {
        ElMessage.error(`文件 ${file.name} 上传失败: ${response.msg || '未知错误'}`)
        uploadResults.push({ status: 'failure' })
      }
    } catch (error) {
      console.error(`上传文件 ${file.name} 出错:`, error)
      ElMessage.error(`文件 ${file.name} 上传失败: ${error.message || '未知错误'}`)
      uploadResults.push({ status: 'failure' })
    }
  }

  const uploadSummary = summarizeMaterialUploadResults(uploadResults)
  isUploading.value = false

  // 全部成功时直接关闭弹窗；只要存在失败，就保留现场给用户查看进度与错误提示。
  if (uploadSummary.shouldCloseDialog) {
    uploadDialogVisible.value = false
  }

  currentPage.value = 1
  await fetchMaterials()
  invalidateMaterialCache()
}

// 预览素材
const handlePreview = async (material) => {
  openMaterialPreview(material)
}

// 删除素材
const handleDelete = (material) => {
  ElMessageBox.confirm(
    `确定要删除素材 ${material.filename} 吗？`,
    '警告',
    {
      confirmButtonText: '确定',
      cancelButtonText: '取消',
      type: 'warning',
    }
  )
    .then(async () => {
      try {
        const response = await materialApi.deleteMaterial(material.id)
        
        if (response.code === 200) {
          if (materials.value.length === 1 && currentPage.value > 1) {
            currentPage.value -= 1
          }
          invalidateMaterialCache()
          await fetchMaterials()
          ElMessage.success('删除成功')
        } else {
          ElMessage.error(response.msg || '删除失败')
        }
      } catch (error) {
        console.error('删除素材出错:', error)
        ElMessage.error('删除失败')
      }
    })
    .catch(() => {
      // 取消删除
    })
}

// 判断文件类型
/**
 * 返回素材展示类型，供表格直接渲染标签。
 */
const getFileType = getMaterialType

/**
 * 列表标签颜色统一走共享实现，避免模板访问未定义函数导致整页渲染中断。
 */
const getFileTypeTag = getMaterialTypeTag

// 组件挂载时获取素材列表
onMounted(() => {
  fetchMaterials()
})
</script>

<style lang="scss" scoped>
@use '@/styles/variables.scss' as *;

@keyframes rotate {
  from {
    transform: rotate(0deg);
  }
  to {
    transform: rotate(360deg);
  }
}

.material-management {
  
  .page-header {
    margin-bottom: 20px;
    
    h1 {
      font-size: 24px;
      font-weight: 500;
      color: $text-primary;
      margin: 0;
    }
  }
  
  .material-list-container {
    background-color: #fff;
    border-radius: 4px;
    box-shadow: 0 2px 12px 0 rgba(0, 0, 0, 0.1);
    padding: 20px;
    
    .material-search {
      display: flex;
      justify-content: space-between;
      align-items: center;
      gap: 16px;
      margin-bottom: 20px;
      
      .material-search__filters {
        display: flex;
        flex: 1;
        flex-wrap: wrap;
        gap: 12px;

        .el-input {
          width: 300px;
        }

        .el-select {
          width: 180px;
        }
      }
      
      .action-buttons {
        display: flex;
        flex-shrink: 0;
        gap: 10px;
        
        .is-loading {
          animation: rotate 1s linear infinite;
        }
      }
    }
    
    .material-list {
      margin-top: 20px;
    }

    .material-pagination {
      display: flex;
      justify-content: flex-end;
      margin-top: 16px;
    }
    
    .empty-data {
      padding: 40px 0;
    }
  }
  
  .material-upload {
    width: 100%;
  }
  
  .preview-container {
    display: flex;
    flex-direction: column;
    gap: 16px;
    padding: 0 20px;

    .preview-meta {
      width: 100%;
      display: flex;
      flex-direction: column;
      gap: 8px;

      .preview-meta__title {
        font-size: 16px;
        font-weight: 600;
        color: $text-primary;
        word-break: break-all;
      }

      .preview-meta__details {
        display: flex;
        flex-wrap: wrap;
        gap: 16px;
        font-size: 13px;
        color: $text-secondary;
      }
    }

    .video-preview,
    .image-preview,
    .audio-preview,
    .document-preview,
    .file-info {
      width: 100%;
      text-align: center;
    }

    .text-preview {
      width: 100%;
      max-height: 60vh;
      overflow: auto;
      padding: 16px;
      border-radius: 8px;
      background-color: #f6f8fa;
      border: 1px solid #e5e7eb;

      pre {
        margin: 0;
        font-size: 13px;
        line-height: 1.6;
        white-space: pre-wrap;
        word-break: break-word;
        color: $text-primary;
      }
    }

    .document-preview__frame {
      width: 100%;
      height: 60vh;
      border: 1px solid #dcdfe6;
      border-radius: 8px;
      background-color: #fff;
    }

    .preview-actions {
      width: 100%;
      display: flex;
      justify-content: flex-end;
      gap: 12px;
    }
  }
}

.upload-form {
  padding: 0 20px;
  
  .form-tip {
    font-size: 12px;
    color: #909399;
    margin-top: 5px;
  }
  
  .upload-demo {
    width: 100%;
  }
}

.dialog-footer {
  padding: 0 20px;
  display: flex;
  justify-content: flex-end;
}

.upload-file-list {
  width: 100%;
}

.upload-file-item {
  border: 1px solid #dcdfe6;
  border-radius: 4px;
  padding: 10px;
  margin-bottom: 10px;
}

.upload-file-item .file-name {
  font-size: 14px;
  color: #606266;
  margin-bottom: 5px;
  display: block;
}

/* 覆盖Element Plus对话框样式 */
:deep(.el-dialog__body) {
  padding: 20px 0;
}

:deep(.el-dialog__header) {
  padding-left: 20px;
  padding-right: 20px;
  margin-right: 0;
}

:deep(.el-dialog__footer) {
  padding-top: 10px;
  padding-bottom: 15px;
}

/* 修改上传进度条样式 */
:deep(.el-progress__text) {
  color: #303133 !important; /* 深灰色字体，确保在各种背景上都可见 */
  font-size: 12px;
}

:deep(.el-progress--line) {
  margin-bottom: 10px;
}

.upload-file-item {
  border: 1px solid #dcdfe6;
  border-radius: 6px; /* 增加圆角 */
  padding: 12px; /* 增加内边距 */
  margin-bottom: 12px; /* 增加外边距 */
  background-color: #fafafa; /* 轻微背景色 */
  transition: box-shadow 0.3s; /* 添加过渡效果 */
}

.upload-file-item:hover {
  box-shadow: 0 2px 8px rgba(0, 0, 0, 0.1); /* 悬停效果 */
}

.upload-file-item .file-name {
  font-size: 14px;
  color: #303133; /* 深灰色字体 */
  margin-bottom: 8px; /* 增加底部间距 */
  display: block;
  font-weight: 500;
}
</style>
