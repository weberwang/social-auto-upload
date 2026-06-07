<template>
  <div class="material-management">
    <div class="page-header">
      <div class="page-header__copy">
        <h1>素材管理</h1>
        <p>集中检索、筛选和维护已上传素材，保持运营素材库清晰可控。</p>
      </div>
      <div class="page-header__meta">
        <span class="page-header__badge">{{ totalMaterials }} 条素材</span>
        <span class="page-header__badge page-header__badge--muted">当前页 {{ materials.length }} 条</span>
      </div>
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
        <el-table :data="materials" class="material-table" style="width: 100%">
          <el-table-column label="UUID" width="220">
            <template #default="scope">
              <div class="material-cell material-cell--uuid">
                <span>{{ scope.row.uuid }}</span>
              </div>
            </template>
          </el-table-column>
          <el-table-column label="文件名" min-width="320">
            <template #default="scope">
              <div class="material-cell material-cell--filename">
                <strong>{{ scope.row.filename }}</strong>
                <span>{{ scope.row.file_path }}</span>
              </div>
            </template>
          </el-table-column>
          <el-table-column label="备注" min-width="240" show-overflow-tooltip>
            <template #default="scope">
              <span
                class="material-remark"
                :class="{ 'material-remark--empty': !scope.row.remark }"
              >
                {{ scope.row.remark || '暂无备注' }}
              </span>
            </template>
          </el-table-column>
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
          <el-table-column prop="upload_time" label="上传时间" min-width="180" />
          <el-table-column label="操作" width="140" align="right">
            <template #default="scope">
              <div class="material-actions">
                <el-button size="small" @click="handlePreview(scope.row)">预览</el-button>
                <el-button size="small" type="danger" @click="handleDelete(scope.row)">删除</el-button>
              </div>
            </template>
          </el-table-column>
        </el-table>
        <div class="material-pagination">
          <span class="material-pagination__summary">{{ paginationSummary }}</span>
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
                <el-input
                  v-model="fileRemarks[file.uid]"
                  type="textarea"
                  :rows="2"
                  maxlength="100"
                  show-word-limit
                  placeholder="请输入素材备注（选填）"
                  class="upload-file-item__remark"
                />
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
import { computed, ref, onMounted } from 'vue'
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
import {
  buildMaterialUploadFormData,
  syncMaterialRemarks
} from '@/composables/materialUploadForm.js'
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

/**
 * 分页区文案单独抽离，避免模板里堆叠字符串拼接逻辑。
 */
const paginationSummary = computed(() => (
  `第 ${currentPage.value} 页，共 ${Math.max(1, Math.ceil(totalMaterials.value / pageSize.value) || 1)} 页`
))

// 对话框控制
const uploadDialogVisible = ref(false)
const {
  previewDialogVisible,
  currentPreviewMaterial: currentMaterial,
  openMaterialPreview
} = useMaterialPreviewDialog()

// 文件上传
const fileList = ref([])
const fileRemarks = ref({})
const uploadProgress = ref({}); // { [uid]: { percentage: 0, speed: '' } }


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
  fileRemarks.value = {}
  uploadProgress.value = {};
  uploadDialogVisible.value = true
}

// 关闭上传对话框时清空变量
const handleUploadDialogClose = () => {
  fileList.value = []
  fileRemarks.value = {}
  uploadProgress.value = {};
}

// 文件选择变更
const handleFileChange = (file, uploadFileList) => {
  fileList.value = uploadFileList;
  fileRemarks.value = syncMaterialRemarks(uploadFileList, fileRemarks.value)
  const newProgress = {};
  for (const f of uploadFileList) {
    newProgress[f.uid] = { percentage: 0, speed: '' };
  }
  uploadProgress.value = newProgress;
}

const handleFileRemove = (file, uploadFileList) => {
  fileList.value = uploadFileList;
  fileRemarks.value = syncMaterialRemarks(uploadFileList, fileRemarks.value)
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

      // 上传表单只提交原始文件和对应备注，避免继续暴露前端自定义文件名能力。
      const formData = buildMaterialUploadFormData({
        file,
        remark: fileRemarks.value[file.uid] || ''
      })
      
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
  padding: 8px 0 24px;
  min-height: calc(100dvh - 40px);
  display: flex;
  flex-direction: column;
  
  .page-header {
    display: flex;
    justify-content: space-between;
    align-items: flex-end;
    gap: 20px;
    margin-bottom: 24px;

    .page-header__copy {
      display: flex;
      flex-direction: column;
      gap: 8px;

      h1 {
        font-size: 30px;
        font-weight: 600;
        letter-spacing: -0.03em;
        color: $text-primary;
        margin: 0;
      }

      p {
        margin: 0;
        max-width: 620px;
        font-size: $font-size-base;
        line-height: 1.7;
        color: $text-secondary;
      }
    }

    .page-header__meta {
      display: flex;
      flex-wrap: wrap;
      justify-content: flex-end;
      gap: 10px;
    }

    .page-header__badge {
      display: inline-flex;
      align-items: center;
      min-height: 38px;
      padding: 0 16px;
      border-radius: 999px;
      background: linear-gradient(135deg, rgba(64, 158, 255, 0.16), rgba(64, 158, 255, 0.08));
      color: $primary-color;
      font-size: $font-size-small;
      font-weight: 600;
    }

    .page-header__badge--muted {
      background: $bg-color;
      border: 1px solid $border-light;
      color: $text-regular;
    }
  }
  
  .material-list-container {
    display: flex;
    flex: 1;
    flex-direction: column;
    background:
      linear-gradient(180deg, rgba(255, 255, 255, 0.98), rgba(248, 250, 252, 0.96));
    border: 1px solid rgba(228, 231, 237, 0.9);
    border-radius: 18px;
    box-shadow: 0 20px 40px rgba(15, 23, 42, 0.06);
    padding: 22px;
    
    .material-search {
      display: flex;
      justify-content: space-between;
      align-items: center;
      gap: 16px;
      margin-bottom: 18px;
      padding: 14px;
      border: 1px solid rgba(228, 231, 237, 0.9);
      border-radius: 16px;
      background: rgba(255, 255, 255, 0.84);
      
      .material-search__filters {
        display: flex;
        flex: 1;
        flex-wrap: wrap;
        gap: 12px;

        .el-input {
          width: 320px;
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
      display: flex;
      flex: 1;
      flex-direction: column;
      min-height: 0;
      margin-top: 20px;
    }

    .material-pagination {
      display: flex;
      position: sticky;
      bottom: 0;
      z-index: 5;
      align-items: center;
      justify-content: space-between;
      gap: 16px;
      margin-top: auto;
      padding-top: 16px;
      padding-bottom: 4px;
      background: linear-gradient(180deg, rgba(248, 250, 252, 0.78), rgba(255, 255, 255, 0.98) 28%);
      backdrop-filter: blur(10px);
      border-top: 1px solid rgba(228, 231, 237, 0.9);
      box-shadow: 0 -12px 30px rgba(15, 23, 42, 0.04);
    }

    .material-pagination__summary {
      font-size: $font-size-small;
      color: $text-secondary;
    }

    .material-table {
      border: 1px solid rgba(228, 231, 237, 0.92);
      border-radius: 18px;
      overflow: hidden;
      background: rgba(255, 255, 255, 0.9);
    }

    :deep(.material-table th.el-table__cell) {
      height: 58px;
      background: #f8fafc;
      color: #64748b;
      font-size: 13px;
      font-weight: 700;
      letter-spacing: 0.02em;
    }

    :deep(.material-table td.el-table__cell) {
      padding-top: 18px;
      padding-bottom: 18px;
      border-bottom: 1px solid rgba(241, 245, 249, 0.96);
      vertical-align: top;
    }

    :deep(.material-table .el-table__row:hover > td.el-table__cell) {
      background: rgba(248, 250, 252, 0.96);
    }

    .material-cell {
      display: flex;
      flex-direction: column;
      gap: 6px;
    }

    .material-cell--uuid {
      font-family: 'JetBrains Mono', 'SFMono-Regular', Consolas, monospace;
      font-size: 12px;
      line-height: 1.7;
      color: #64748b;
      word-break: break-all;
    }

    .material-cell--filename {
      strong {
        font-size: 14px;
        font-weight: 600;
        line-height: 1.5;
        color: $text-primary;
        word-break: break-all;
      }

      span {
        font-size: 12px;
        line-height: 1.6;
        color: #94a3b8;
        word-break: break-all;
      }
    }

    .material-remark {
      display: inline-flex;
      align-items: center;
      min-height: 36px;
      padding: 8px 12px;
      border-radius: 12px;
      background: #f8fafc;
      color: $text-regular;
      font-size: 13px;
      line-height: 1.5;
    }

    .material-remark--empty {
      color: #94a3b8;
      background: #f1f5f9;
    }

    .material-actions {
      display: flex;
      justify-content: flex-end;
      gap: 8px;
    }
    
    .empty-data {
      padding: 56px 0 44px;
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
  margin-bottom: 10px;
  display: block;
}

.upload-file-item__remark {
  margin-bottom: 10px;
}

@media (max-width: 1200px) {
  .material-management {
    .page-header {
      flex-direction: column;
      align-items: flex-start;

      .page-header__meta {
        justify-content: flex-start;
      }
    }
  }
}

@media (max-width: 768px) {
  .material-management {
    .page-header {
      .page-header__copy {
        h1 {
          font-size: 26px;
        }
      }
    }

    .material-list-container {
      padding: 16px;
      border-radius: 16px;

      .material-search {
        flex-direction: column;
        align-items: stretch;

        .material-search__filters {
          .el-input,
          .el-select {
            width: 100%;
          }
        }

        .action-buttons {
          width: 100%;

          .el-button {
            flex: 1;
          }
        }
      }

      .material-pagination {
        flex-direction: column;
        align-items: flex-start;
      }
    }
  }
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
