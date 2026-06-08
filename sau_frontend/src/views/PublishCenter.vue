<template>
  <div class="publish-center">
    <PublishTabBar
      :tabs="tabs"
      :active-tab="activeTab"
      :platforms="platforms"
      :batch-publishing="batchPublishing"
      :draft-dialog-visible="draftDialogVisible"
      :draft-loading="draftLoading"
      :draft-items="draftItems"
      :current-draft-name="currentDraftName"
      @select-tab="activeTab = $event"
      @remove-tab="removeTab"
      @copy-tab="addTab"
      @batch-publish="batchPublish"
      @save-draft="saveDraft"
      @open-draft="openDraftDialog"
      @refresh-drafts="refreshDrafts"
      @load-draft="loadDraft"
      @remove-draft="removeDraft"
      @update:draft-visible="draftDialogVisible = $event"
    />

    <div class="publish-content">
      <div class="tab-content-wrapper">
        <div 
          v-for="tab in tabs" 
          :key="tab.name"
          v-show="activeTab === tab.name"
          class="tab-content"
        >
          <div v-if="tab.publishStatus" class="publish-status">
            <el-alert
              :title="tab.publishStatus.message"
              :type="tab.publishStatus.type"
              :closable="false"
              show-icon
            />
          </div>

          <div class="upload-section">
            <h3>{{ getUploadSectionTitle(tab.contentType) }}</h3>
            <div class="upload-options">
              <el-button type="primary" @click="openMaterialLibrary(tab)" class="upload-btn">
                <el-icon><Upload /></el-icon>
                {{ getUploadButtonText(tab.contentType) }}
              </el-button>
            </div>
            
            <div v-if="tab.fileList.length > 0" class="uploaded-files">
              <h4>已选素材：</h4>
              <div class="file-list">
                <div v-for="(file, index) in tab.fileList" :key="index" class="file-item">
                  <el-link :href="file.url" target="_blank" type="primary">{{ file.name }}</el-link>
                  <span class="file-size">{{ (file.size / 1024 / 1024).toFixed(2) }}MB</span>
                  <el-button size="small" @click="openSelectedFilePreview(file)">预览</el-button>
                  <el-button type="danger" size="small" @click="removeFile(tab, index)">删除</el-button>
                </div>
              </div>
            </div>
          </div>

          <el-dialog
            v-model="localUploadVisible"
            title="上传素材"
            width="600px"
            class="local-upload-dialog"
          >
            <el-upload
              class="video-upload"
              drag
              :auto-upload="true"
              :action="`${apiBaseUrl}/upload`"
              :on-success="(response, file) => handleUploadSuccess(response, file, currentUploadTab)"
              :on-error="handleUploadError"
              multiple
              :accept="getUploadAccept(currentUploadContentType)"
              :headers="authHeaders"
            >
              <el-icon class="el-icon--upload"><Upload /></el-icon>
              <div class="el-upload__text">
                将{{ getUploadSectionTitle(currentUploadContentType) }}文件拖到此处，或<em>点击上传</em>
              </div>
              <template #tip>
                <div class="el-upload__tip">
                  {{ getUploadTipText(currentUploadContentType) }}
                </div>
              </template>
            </el-upload>
          </el-dialog>

          <PublishBatchProgressDialog
            :visible="batchPublishDialogVisible"
            :progress="publishProgress"
            :current-tab="currentPublishingTab"
            :results="publishResults"
            @cancel="cancelBatchPublish"
            @update:visible="batchPublishDialogVisible = $event"
          />

          <PublishMaterialSelectorDialog
            :visible="materialLibraryVisible"
            :rows="currentUploadMaterialRows"
            :platform-name="currentUploadPlatformName"
            :platform-supports-image-text="currentUploadPlatformSupportsImageText"
            :selected-material-ids="selectedMaterials"
            :empty-state="materialLibraryEmptyState"
            @update:visible="materialLibraryVisible = $event"
            @update:selected-material-ids="selectedMaterials = $event"
            @preview="openMaterialLibraryPreview"
            @upload="openLocalUploadFromMaterialLibrary"
            @confirm="confirmMaterialSelection"
          />

          <div class="account-section">
            <h3>账号</h3>
            <div class="account-select-wrapper">
              <el-select
                :model-value="tab.selectedAccounts[0]"
                placeholder="请选择账号"
                class="account-select"
                @change="handleAccountChange(tab, $event)"
              >
                <el-option
                  v-for="account in getAvailableAccountsForTab(tab)"
                  :key="account.id"
                  :label="account.name"
                  :value="account.id"
                />
                <template #empty>
                  <div class="account-empty-state">
                    <span>当前平台暂无账号，请先去添加</span>
                    <el-button type="primary" link @click="goToAccountManagement">去添加</el-button>
                  </div>
                </template>
              </el-select>
              <p v-if="getAvailableAccountsForTab(tab).length === 0" class="account-empty-tip">
                当前平台暂无账号，请先去添加
              </p>
            </div>
          </div>

          <div class="platform-section">
            <h3>平台</h3>
            <el-radio-group v-model="tab.selectedPlatform" class="platform-radios" @change="handlePlatformChange(tab)">
              <el-radio 
                v-for="platform in platforms" 
                :key="platform.key"
                :label="platform.key"
                class="platform-radio"
              >
                {{ platform.name }}
              </el-radio>
            </el-radio-group>
          </div>

          <div class="content-type-section">
            <h3>内容类型</h3>
            <el-radio-group v-model="tab.contentType" class="platform-radios" @change="handleContentTypeChange(tab)">
              <el-radio
                v-for="contentType in getContentTypeOptions(tab)"
                :key="contentType.value"
                :label="contentType.value"
                class="platform-radio"
              >
                {{ contentType.label }}
              </el-radio>
            </el-radio-group>
          </div>

          <div class="original-section">
            <el-checkbox
              v-model="tab.isOriginal"
              label="声明原创"
              class="original-checkbox"
            />
          </div>

          <div v-if="tab.selectedPlatform === 2 && !isImageTextTab(tab)" class="draft-section">
            <el-checkbox
              v-model="tab.isDraft"
              label="视频号仅保存草稿(用手机发布)"
              class="draft-checkbox"
            />
          </div>

          <div v-if="tab.selectedPlatform === 3 && !isImageTextTab(tab)" class="product-section">
            <h3>商品链接</h3>
            <el-input
              v-model="tab.productTitle"
              type="text"
              :rows="1"
              placeholder="请输入商品名称"
              maxlength="200"
              class="product-name-input"
            />
            <el-input
              v-model="tab.productLink"
              type="text"
              :rows="1"
              placeholder="请输入商品链接"
              maxlength="200"
              class="product-link-input"
            />
          </div>

          <BilibiliPublishFields
            v-if="tab.selectedPlatform === 5 && !isImageTextTab(tab)"
            v-model:description="tab.description"
            v-model:bilibili-tid="tab.bilibiliTid"
          />

          <div class="title-section">
            <h3>标题</h3>
            <el-input
              v-model="tab.title"
              type="textarea"
              :rows="3"
              placeholder="请输入标题"
              maxlength="100"
              show-word-limit
              class="title-input"
            />
          </div>

          <div v-if="isImageTextTab(tab)" class="note-section">
            <h3>图文正文</h3>
            <el-input
              v-model="tab.noteContent"
              type="textarea"
              :rows="6"
              :placeholder="getNotePlaceholder(getPlatformName(tab.selectedPlatform))"
              maxlength="1000"
              show-word-limit
              class="title-input"
            />
          </div>

          <div class="topic-section">
            <h3>话题</h3>
            <div class="topic-display">
              <div class="selected-topics">
                <el-tag
                  v-for="(topic, index) in tab.selectedTopics"
                  :key="index"
                  closable
                  @close="removeTopic(tab, index)"
                  class="topic-tag"
                >
                  #{{ topic }}
                </el-tag>
              </div>
              <el-button 
                type="primary" 
                plain 
                @click="openTopicDialog(tab)"
                class="select-topic-btn"
              >
                添加话题
              </el-button>
            </div>
          </div>

          <el-dialog
            v-model="topicDialogVisible"
            title="添加话题"
            width="600px"
            class="topic-dialog"
          >
            <div class="topic-dialog-content">
              <div class="custom-topic-input">
                <el-input
                  v-model="customTopic"
                  placeholder="输入自定义话题"
                  class="custom-input"
                >
                  <template #prepend>#</template>
                </el-input>
                <el-button type="primary" @click="addCustomTopic">添加</el-button>
              </div>

              <div class="recommended-topics">
                <h4>推荐话题</h4>
                <div class="topic-grid">
                  <el-button
                    v-for="topic in recommendedTopics"
                    :key="topic"
                    :type="currentTab?.selectedTopics?.includes(topic) ? 'primary' : 'default'"
                    @click="toggleRecommendedTopic(topic)"
                    class="topic-btn"
                  >
                    {{ topic }}
                  </el-button>
                </div>
              </div>
            </div>

            <template #footer>
              <div class="dialog-footer">
                <el-button @click="topicDialogVisible = false">取消</el-button>
                <el-button type="primary" @click="confirmTopicSelection">确定</el-button>
              </div>
            </template>
          </el-dialog>

          <div class="schedule-section">
            <h3>定时发布</h3>
            <div class="schedule-controls">
              <el-switch
                v-model="tab.scheduleEnabled"
                active-text="定时发布"
                inactive-text="立即发布"
              />
              <div v-if="tab.scheduleEnabled" class="schedule-settings">
                <div class="schedule-item">
                  <span class="label">每天发布内容数：</span>
                  <el-select v-model="tab.videosPerDay" placeholder="选择发布数量">
                    <el-option
                      v-for="num in 55"
                      :key="num"
                      :label="num"
                      :value="num"
                    />
                  </el-select>
                </div>
                <div class="schedule-item">
                  <span class="label">每天发布时间：</span>
                  <el-time-select
                    v-for="(time, index) in tab.dailyTimes"
                    :key="index"
                    v-model="tab.dailyTimes[index]"
                    start="00:00"
                    step="00:30"
                    end="23:30"
                    placeholder="选择时间"
                  />
                  <el-button
                    v-if="tab.dailyTimes.length < tab.videosPerDay"
                    type="primary"
                    size="small"
                    @click="tab.dailyTimes.push('10:00')"
                  >
                    添加时间
                  </el-button>
                </div>
                <div class="schedule-item">
                  <span class="label">开始天数：</span>
                  <el-select v-model="tab.startDays" placeholder="选择开始天数">
                    <el-option :label="'明天'" :value="0" />
                    <el-option :label="'后天'" :value="1" />
                  </el-select>
                </div>
              </div>
            </div>
          </div>

          <div class="action-buttons">
            <el-button size="small" @click="cancelPublish(tab)">取消</el-button>
            <el-button
              size="small"
              type="primary"
              @click="confirmPublish(tab)"
              :loading="tab.publishing || false"
            >
              {{ tab.publishing ? '发布中...' : '发布' }}
            </el-button>
          </div>
        </div>
      </div>
    </div>

    <MaterialPreviewDialog
      v-model="previewDialogVisible"
      :material="currentPreviewMaterial"
    />
  </div>
</template>

<script setup>
import { ref, reactive, computed, onMounted } from 'vue'
import { useRouter } from 'vue-router'
import { Upload } from '@element-plus/icons-vue'
import { ElMessage } from 'element-plus'
import { accountApi } from '@/api/account'
import PublishBatchProgressDialog from '@/components/PublishBatchProgressDialog.vue'
import BilibiliPublishFields from '@/components/BilibiliPublishFields.vue'
import MaterialPreviewDialog from '@/components/MaterialPreviewDialog.vue'
import PublishMaterialSelectorDialog from '@/components/PublishMaterialSelectorDialog.vue'
import PublishTabBar from '@/components/PublishTabBar.vue'
import { useMaterialPreviewDialog } from '@/composables/useMaterialPreviewDialog.js'
import { usePublishDrafts } from '@/composables/usePublishDrafts.js'
import { useAccountStore } from '@/stores/account'
import { useAppStore } from '@/stores/app'
import {
  buildPublishTabLabel,
  PUBLISH_PLATFORM_OPTIONS,
  buildPublishPayload,
  getAvailableAccountsForPlatform,
  getDefaultSelectedAccountIdsForPlatform,
  getMismatchedAccountNamesForPlatform,
  getPublishPlatformOption,
  getSupportedContentTypesForPlatform,
  PUBLISH_CONTENT_TYPE_IMAGE_TEXT,
  PUBLISH_CONTENT_TYPE_LABEL_BY_VALUE,
  resolveSupportedContentType
} from '@/constants/publishPlatforms'
import {
  PUBLISH_CONTENT_TYPE_VIDEO,
  buildPublishMaterialSelectionRows,
  buildDisplayFileList,
  createPublishFileFromMaterial,
  createPublishFileFromUpload,
  filterFilesByContentType,
  getMaterialLibraryEmptyState,
  getEmptyFileMessage,
  getNotePlaceholder,
  getUploadAccept,
  getUploadButtonText,
  getUploadSectionTitle,
  getUploadTipText
} from '@/constants/publishMaterials'
import { restorePublishDraftWorkspace } from '@/constants/publishDrafts'
import {
  createCopiedPublishTab,
  createCopiedPublishTabsForPlatforms,
  createEmptyPublishTab
} from '@/constants/publishTabCopy.js'
import { materialApi } from '@/api/material'
import { http } from '@/utils/request'

const apiBaseUrl = import.meta.env.VITE_API_BASE_URL || 'http://localhost:5409'

const authHeaders = computed(() => ({
  Authorization: `Bearer ${localStorage.getItem('token') || ''}`
}))

const activeTab = ref('tab1')

let tabCounter = 1

const appStore = useAppStore()
const router = useRouter()

const localUploadVisible = ref(false)
const materialLibraryVisible = ref(false)
const currentUploadTab = ref(null)
const selectedMaterials = ref([])
const materials = computed(() => appStore.materials)
const currentUploadContentType = computed(() => currentUploadTab.value?.contentType || PUBLISH_CONTENT_TYPE_VIDEO)
const currentUploadPlatformKey = computed(() => currentUploadTab.value?.selectedPlatform || 0)
const currentUploadMaterialRows = computed(() => (
  buildPublishMaterialSelectionRows(materials.value, currentUploadPlatformKey.value)
))
const materialLibraryEmptyState = computed(() => (
  getMaterialLibraryEmptyState(materials.value, currentUploadPlatformKey.value)
))
const {
  previewDialogVisible,
  currentPreviewMaterial,
  openMaterialPreview,
  openPublishFilePreview
} = useMaterialPreviewDialog()

const batchPublishing = ref(false)

const platforms = PUBLISH_PLATFORM_OPTIONS

/**
 * 返回平台展示名称，供图文正文占位文案和提示信息复用。
 */
const getPlatformName = (platformKey) => getPublishPlatformOption(platformKey)?.name || '当前平台'
const currentUploadPlatformName = computed(() => getPlatformName(currentUploadPlatformKey.value))
const currentUploadPlatformSupportsImageText = computed(() => (
  getSupportedContentTypesForPlatform(currentUploadPlatformKey.value).includes(PUBLISH_CONTENT_TYPE_IMAGE_TEXT)
))

/**
 * 返回当前 Tab 可选择的内容类型列表。
 */
const getContentTypeOptions = (tab) => {
  return getSupportedContentTypesForPlatform(tab.selectedPlatform).map((contentType) => ({
    value: contentType,
    label: PUBLISH_CONTENT_TYPE_LABEL_BY_VALUE[contentType] || contentType
  }))
}

/**
 * 平台支持视频/图文双模式时，统一判断当前 Tab 是否处于图文模式。
 */
const isImageTextTab = (tab) => tab.contentType === PUBLISH_CONTENT_TYPE_IMAGE_TEXT

const tabs = reactive([
  createEmptyPublishTab()
])

const currentTab = ref(null)

const accountStore = useAccountStore()

/**
 * 页签标题统一跟随“账号 + 平台”规则变化，避免不同交互入口各自维护一套标题逻辑。
 */
const syncTabLabel = (tab) => {
  tab.label = buildPublishTabLabel(
    tab.selectedPlatform,
    tab.selectedAccounts,
    accountStore.accounts
  )
}

/**
 * 账号列表刷新或草稿整体回填后，需要批量重算所有页签标题。
 */
const syncAllTabLabels = () => {
  tabs.forEach((tab) => syncTabLabel(tab))
}

/**
 * 下拉账号列表按当前 Tab 的平台实时过滤，避免切平台后看到脏选项。
 */
const getAvailableAccountsForTab = (tab) => (
  getAvailableAccountsForPlatform(accountStore.accounts, tab.selectedPlatform)
)

/**
 * 账号选择改为下拉单选后，统一保证每个 Tab 至少优先选中当前平台的第一个账号。
 */
const syncTabSelectedAccount = (tab) => {
  if (accountStore.accounts.length === 0) {
    syncTabLabel(tab)
    return
  }

  tab.selectedAccounts = getDefaultSelectedAccountIdsForPlatform(
    accountStore.accounts,
    tab.selectedAccounts,
    tab.selectedPlatform
  )
  syncTabLabel(tab)
}

/**
 * 账号列表就绪后，批量补齐全部 Tab 的默认账号和对应标题。
 */
const syncAllTabsAccountSelection = () => {
  tabs.forEach((tab) => syncTabSelectedAccount(tab))
}

/**
 * 发布中心会被用户直接打开，因此这里兜底拉一次账号列表，避免依赖别的页面提前填充 store。
 */
const loadPublishCenterAccounts = async () => {
  if (accountStore.accounts.length > 0) {
    syncAllTabsAccountSelection()
    return
  }

  try {
    const response = await accountApi.getAccounts()
    if (response.code === 200) {
      accountStore.setAccounts(response.data)
      syncAllTabsAccountSelection()
    }
  } catch (error) {
    console.error('获取发布中心账号列表失败:', error)
  }
}

const topicDialogVisible = ref(false)
const customTopic = ref('')

const recommendedTopics = [
  '游戏', '电影', '音乐', '美食', '旅行', '文化',
  '科技', '生活', '娱乐', '体育', '教育', '艺术',
  '健康', '时尚', '美妆', '摄影', '宠物', '汽车'
]

/**
 * 草稿加载会直接替换整个工作区，因此需要一次性重建 Tab、激活项和临时弹窗状态。
 */
const applyDraftWorkspace = (workspace) => {
  const restoredWorkspace = restorePublishDraftWorkspace(workspace)
  tabs.splice(0, tabs.length, ...restoredWorkspace.tabs)
  if (accountStore.accounts.length > 0) {
    syncAllTabsAccountSelection()
  } else {
    syncAllTabLabels()
  }
  activeTab.value = restoredWorkspace.activeTab
  tabCounter = restoredWorkspace.tabCounter
  currentTab.value = null
  currentUploadTab.value = null
  selectedMaterials.value = []
  localUploadVisible.value = false
  materialLibraryVisible.value = false
  topicDialogVisible.value = false
}

const {
  currentDraftName,
  draftDialogVisible,
  draftItems,
  draftLoading,
  openDraftDialog,
  refreshDrafts,
  removeDraft,
  saveDraft,
  loadDraft
} = usePublishDrafts({
  getTabs: () => tabs,
  getActiveTab: () => activeTab.value,
  getTabCounter: () => tabCounter,
  applyWorkspace: applyDraftWorkspace
})

/**
 * 复制当前激活标签到目标平台，新标签只保留跨平台可复用的内容字段。
 */
const addTab = (platformKey) => {
  const sourceTab = tabs.find((tab) => tab.name === activeTab.value)
  if (!sourceTab) {
    ElMessage.warning('请先选择要复制的标签')
    return
  }

  if (platformKey === 'copy_all') {
    const copiedTabs = createCopiedPublishTabsForPlatforms(
      sourceTab,
      platforms.map((platform) => platform.key),
      tabCounter + 1
    )

    if (copiedTabs.length === 0) {
      ElMessage.warning('当前没有可复制的其他平台')
      return
    }

    tabCounter += copiedTabs.length
    tabs.push(...copiedTabs)
    copiedTabs.forEach((tab) => syncTabSelectedAccount(tab))
    activeTab.value = copiedTabs[copiedTabs.length - 1].name
    ElMessage.success(`已复制到${copiedTabs.length}个平台`)
    return
  }

  tabCounter++
  const newTab = createCopiedPublishTab(sourceTab, platformKey, tabCounter)
  tabs.push(newTab)
  syncTabSelectedAccount(newTab)
  activeTab.value = newTab.name
  ElMessage.success(`已复制到新的${getPlatformName(newTab.selectedPlatform)}标签`)
}

const removeTab = (tabName) => {
  const index = tabs.findIndex(tab => tab.name === tabName)
  if (index > -1) {
    tabs.splice(index, 1)
    if (activeTab.value === tabName && tabs.length > 0) {
      activeTab.value = tabs[0].name
    }
  }
}

const handleUploadSuccess = (response, file, tab) => {
  if (response.code === 200) {
    const fileInfo = createPublishFileFromUpload(response, file, materialApi.getMaterialPreviewUrl)
    tab.fileList.push(fileInfo)
    tab.displayFileList = buildDisplayFileList(tab.fileList)
    ElMessage.success('文件上传成功')
    return
  }
  ElMessage.error(response.msg || '上传失败')
}

const handleUploadError = () => {
  ElMessage.error('文件上传失败')
}

const removeFile = (tab, index) => {
  tab.fileList.splice(index, 1)
  tab.displayFileList = buildDisplayFileList(tab.fileList)
  ElMessage.success('文件删除成功')
}

const openSelectedFilePreview = (file) => {
  openPublishFilePreview(file)
}

const openMaterialLibraryPreview = (material) => {
  openMaterialPreview(material)
}

const openTopicDialog = (tab) => {
  currentTab.value = tab
  topicDialogVisible.value = true
}

const addCustomTopic = () => {
  if (!customTopic.value.trim()) {
    ElMessage.warning('请输入话题内容')
    return
  }
  if (currentTab.value && !currentTab.value.selectedTopics.includes(customTopic.value.trim())) {
    currentTab.value.selectedTopics.push(customTopic.value.trim())
    customTopic.value = ''
    ElMessage.success('话题添加成功')
  } else {
    ElMessage.warning('话题已存在')
  }
}

const toggleRecommendedTopic = (topic) => {
  if (!currentTab.value) return
  
  const index = currentTab.value.selectedTopics.indexOf(topic)
  if (index > -1) {
    currentTab.value.selectedTopics.splice(index, 1)
  } else {
    currentTab.value.selectedTopics.push(topic)
  }
}

const removeTopic = (tab, index) => {
  tab.selectedTopics.splice(index, 1)
}

const confirmTopicSelection = () => {
  topicDialogVisible.value = false
  customTopic.value = ''
  currentTab.value = null
  ElMessage.success('添加话题完成')
}

/**
 * 账号选择改为下拉单选后，值变更时只保留一个账号，并在空值场景回退到平台默认账号。
 */
const handleAccountChange = (tab, accountId) => {
  tab.selectedAccounts = accountId ? [accountId] : []
  syncTabSelectedAccount(tab)
}

const goToAccountManagement = () => {
  router.push('/account-management')
}

const handlePlatformChange = (tab) => {
  syncTabSelectedAccount(tab)
  tab.contentType = resolveSupportedContentType(tab.selectedPlatform, tab.contentType)
  const filteredFiles = filterFilesByContentType(tab.fileList, tab.contentType)
  if (filteredFiles.length !== tab.fileList.length) {
    ElMessage.warning('已自动移除与当前平台内容类型不兼容的素材')
  }
  tab.fileList = filteredFiles
  tab.displayFileList = buildDisplayFileList(tab.fileList)
  if (tab.selectedAccounts.length === 0) {
    ElMessage.warning('当前平台暂无账号，请先去账号管理添加')
  }
}

/**
 * 切换内容类型时，需要同步清理不兼容素材和图文正文，避免旧状态误入新链路。
 */
const handleContentTypeChange = (tab) => {
  tab.contentType = resolveSupportedContentType(tab.selectedPlatform, tab.contentType)
  const filteredFiles = filterFilesByContentType(tab.fileList, tab.contentType)
  if (filteredFiles.length !== tab.fileList.length) {
    ElMessage.warning('已自动移除与当前内容类型不兼容的素材')
  }
  tab.fileList = filteredFiles
  tab.displayFileList = buildDisplayFileList(tab.fileList)
  if (tab.contentType !== PUBLISH_CONTENT_TYPE_IMAGE_TEXT) {
    tab.noteContent = ''
  }
}

const cancelPublish = (tab) => {
  ElMessage.info('已取消发布')
}

const confirmPublish = async (tab) => {
  if (tab.publishing) {
    throw new Error('正在发布中，请稍候...')
  }

  tab.publishing = true

  if (tab.fileList.length === 0) {
    const emptyFileMessage = getEmptyFileMessage(tab.contentType)
    ElMessage.error(emptyFileMessage)
    tab.publishing = false
    throw new Error(emptyFileMessage)
  }
  if (!tab.title.trim()) {
    ElMessage.error('请输入标题')
    tab.publishing = false
    throw new Error('请输入标题')
  }
  if (!tab.selectedPlatform) {
    ElMessage.error('请选择发布平台')
    tab.publishing = false
    throw new Error('请选择发布平台')
  }
  if (tab.selectedAccounts.length === 0) {
    ElMessage.error('请选择发布账号')
    tab.publishing = false
    throw new Error('请选择发布账号')
  }
  const mismatchedAccountNames = getMismatchedAccountNamesForPlatform(
    accountStore.accounts,
    tab.selectedAccounts,
    tab.selectedPlatform
  )
  if (mismatchedAccountNames.length > 0) {
    const message = `所选账号与当前平台不匹配：${mismatchedAccountNames.join('、')}`
    ElMessage.error(message)
    tab.publishing = false
    throw new Error(message)
  }
  if (isImageTextTab(tab) && !tab.noteContent.trim()) {
    ElMessage.error('请输入图文正文')
    tab.publishing = false
    throw new Error('请输入图文正文')
  }
  if (tab.selectedPlatform === 5 && !tab.description.trim()) {
    ElMessage.error('请输入B站简介')
    tab.publishing = false
    throw new Error('请输入B站简介')
  }
  if (tab.selectedPlatform === 5 && (!Number.isInteger(tab.bilibiliTid) || tab.bilibiliTid <= 0)) {
    ElMessage.error('请选择B站分区')
    tab.publishing = false
    throw new Error('请选择B站分区')
  }

  const publishData = buildPublishPayload(tab, accountStore.accounts)

  try {
    const data = await http.post('/postVideo', publishData)
    tab.publishStatus = {
      message: '发布成功',
      type: 'success'
    }
    tab.fileList = []
    tab.displayFileList = []
    tab.title = ''
    tab.description = ''
    tab.noteContent = ''
    tab.bilibiliTid = null
    tab.selectedTopics = []
    tab.selectedAccounts = []
    tab.scheduleEnabled = false
    syncTabSelectedAccount(tab)
  } catch (error) {
    console.error('发布错误:', error)
    tab.publishStatus = {
      message: `发布失败：${error.message || '请检查网络连接'}`,
      type: 'error'
    }
    throw error
  } finally {
    tab.publishing = false
  }
}

/**
 * 选择素材直接进入素材列表弹窗；上传能力作为弹窗内动作提供，不再额外插入来源切换步骤。
 */
const openMaterialLibrary = async (tab) => {
  if (tab) {
    currentUploadTab.value = tab
  }
  if (materials.value.length === 0) {
    try {
      const response = await materialApi.getAllMaterials()
      if (response.code === 200) {
        appStore.setMaterials(response.data)
      } else {
        ElMessage.error('获取素材列表失败')
        return
      }
    } catch (error) {
      console.error('获取素材列表出错:', error)
      ElMessage.error('获取素材列表失败')
      return
    }
  }
  
  selectedMaterials.value = []
  materialLibraryVisible.value = true
}

const openLocalUploadFromMaterialLibrary = () => {
  materialLibraryVisible.value = false
  localUploadVisible.value = true
}

const confirmMaterialSelection = () => {
  if (selectedMaterials.value.length === 0) {
    ElMessage.warning('请选择至少一个素材')
    return
  }
  
  if (currentUploadTab.value) {
    const selectedRows = selectedMaterials.value
      .map((materialId) => currentUploadMaterialRows.value.find((row) => row.id === materialId))
      .filter((material) => material?.compatible)

    const selectionContentTypes = [...new Set(selectedRows.map((material) => material.selectionContentType).filter(Boolean))]
    if (selectionContentTypes.length > 1) {
      ElMessage.error('图片和视频素材不能同时选择，请分开发布。')
      return
    }

    const targetContentType = selectionContentTypes[0]
    if (targetContentType && currentUploadTab.value.contentType !== targetContentType) {
      currentUploadTab.value.contentType = targetContentType
      handleContentTypeChange(currentUploadTab.value)
    }

    selectedRows.forEach((material) => {
      const fileInfo = createPublishFileFromMaterial(material, materialApi.getMaterialPreviewUrl)
      const exists = currentUploadTab.value.fileList.some((file) => file.path === fileInfo.path)
      if (!exists) {
        currentUploadTab.value.fileList.push(fileInfo)
      }
    })

    currentUploadTab.value.displayFileList = buildDisplayFileList(currentUploadTab.value.fileList)
  }
  
  const addedCount = selectedMaterials.value.length
  materialLibraryVisible.value = false
  selectedMaterials.value = []
  currentUploadTab.value = null
  ElMessage.success(`已添加 ${addedCount} 个素材`)
}

const batchPublishDialogVisible = ref(false)
const currentPublishingTab = ref(null)
const publishProgress = ref(0)
const publishResults = ref([])
const isCancelled = ref(false)

const cancelBatchPublish = () => {
  isCancelled.value = true
  ElMessage.info('正在取消发布...')
}

const batchPublish = async () => {
  if (batchPublishing.value) return
  
  batchPublishing.value = true
  currentPublishingTab.value = null
  publishProgress.value = 0
  publishResults.value = []
  isCancelled.value = false
  batchPublishDialogVisible.value = true
  
  try {
    for (let i = 0; i < tabs.length; i++) {
      if (isCancelled.value) {
        publishResults.value.push({
          label: tabs[i].label,
          status: 'cancelled',
          message: '已取消'
        })
        continue
      }

      const tab = tabs[i]
      currentPublishingTab.value = tab
      publishProgress.value = Math.floor((i / tabs.length) * 100)
      
      try {
        await confirmPublish(tab)
        publishResults.value.push({
          label: tab.label,
          status: 'success',
          message: '发布成功'
        })
      } catch (error) {
        publishResults.value.push({
          label: tab.label,
          status: 'error',
          message: error.message
        })
      }
    }
    
    publishProgress.value = 100
    
    const successCount = publishResults.value.filter(r => r.status === 'success').length
    const failCount = publishResults.value.filter(r => r.status === 'error').length
    const cancelCount = publishResults.value.filter(r => r.status === 'cancelled').length
    
    if (isCancelled.value) {
      ElMessage.warning(`发布已取消：${successCount}个成功，${failCount}个失败，${cancelCount}个未执行`)
    } else if (failCount > 0) {
      ElMessage.error(`发布完成：${successCount}个成功，${failCount}个失败`)
    } else {
      ElMessage.success('所有Tab发布成功')
      setTimeout(() => {
        batchPublishDialogVisible.value = false
      }, 1000)
    }
    
  } catch (error) {
    console.error('批量发布出错:', error)
    ElMessage.error('批量发布出错，请重试')
  } finally {
    batchPublishing.value = false
    isCancelled.value = false
  }
}

onMounted(() => {
  loadPublishCenterAccounts()
})
</script>

<style lang="scss" scoped>
@use '@/styles/variables.scss' as *;

.publish-center {
  display: flex;
  flex-direction: column;
  height: 100%;
  
  .dialog-footer {
    text-align: right;
  }
  
  // 内容区域
  .publish-content {
    flex: 1;
    background-color: #fff;
    border-radius: 4px;
    box-shadow: 0 2px 12px 0 rgba(0, 0, 0, 0.1);
    padding: 20px;
    
    .tab-content-wrapper {
      display: flex;
      justify-content: center;
      
      .tab-content {
        width: 100%;
        max-width: 800px;
        
        h3 {
          font-size: 16px;
          font-weight: 500;
          color: $text-primary;
          margin: 0 0 10px 0;
        }
        
        .upload-section,
        .account-section,
        .platform-section,
        .title-section,
        .product-section,
        .topic-section,
        .schedule-section {
          margin-bottom: 30px;
        }

        .product-section {
          .product-name-input,
          .product-link-input {
            margin-bottom: 5px;
          }
        }
        
        .video-upload {
          width: 100%;
          
          :deep(.el-upload-dragger) {
            width: 100%;
            height: 180px;
          }
        }
        
        .account-select-wrapper {
          display: flex;
          flex-direction: column;
          gap: 8px;
          max-width: 420px;

          .account-select {
            width: 100%;
          }

          .account-empty-state {
            display: flex;
            align-items: center;
            justify-content: space-between;
            gap: 12px;
            color: $text-secondary;
          }

          .account-empty-tip {
            margin: 0;
            font-size: 13px;
            color: $text-secondary;
          }
        }
        
        .platform-buttons {
          display: flex;
          gap: 10px;
          flex-wrap: wrap;
          
          .platform-btn {
            min-width: 80px;
          }
        }
        
        .title-input {
          max-width: 600px;
        }
        
        .topic-display {
          display: flex;
          flex-direction: column;
          gap: 12px;
          
          .selected-topics {
            display: flex;
            flex-wrap: wrap;
            gap: 8px;
            min-height: 32px;
            
            .topic-tag {
              font-size: 14px;
            }
          }
          
          .select-topic-btn {
            align-self: flex-start;
          }
        }
        
        .schedule-controls {
          display: flex;
          flex-direction: column;
          gap: 15px;

          .schedule-settings {
            margin-top: 15px;
            padding: 15px;
            background-color: #f5f7fa;
            border-radius: 4px;

            .schedule-item {
              display: flex;
              align-items: center;
              margin-bottom: 15px;

              &:last-child {
                margin-bottom: 0;
              }

              .label {
                min-width: 120px;
                margin-right: 10px;
              }

              .el-time-select {
                margin-right: 10px;
              }

              .el-button {
                margin-left: 10px;
              }
            }
          }
        }
        
        .action-buttons {
          display: flex;
          justify-content: flex-end;
          gap: 10px;
          margin-top: 30px;
          padding-top: 20px;
          border-top: 1px solid #ebeef5;
        }

        .draft-section {
          margin: 20px 0;

          .draft-checkbox {
            display: block;
            margin: 10px 0;
          }
        }

        .original-section {
          margin: 10px 0 20px;

          .original-checkbox {
            display: block;
            margin: 10px 0;
          }
        }
      }
    }
  }

  // 已上传文件列表样式
  .uploaded-files {
    margin-top: 20px;
    
    h4 {
      font-size: 16px;
      font-weight: 500;
      margin-bottom: 12px;
      color: #303133;
    }
    
    .file-list {
      display: flex;
      flex-direction: column;
      gap: 10px;
      
      .file-item {
        display: flex;
        align-items: center;
        padding: 10px 15px;
        background-color: #f5f7fa;
        border-radius: 4px;
        
        .el-link {
          margin-right: 10px;
          max-width: 300px;
          overflow: hidden;
          text-overflow: ellipsis;
          white-space: nowrap;
        }
        
        .file-size {
          color: #909399;
          font-size: 13px;
          margin-right: auto;
        }
      }
    }
  }
  
  // 添加话题弹窗样式
  .topic-dialog {
    .topic-dialog-content {
      .custom-topic-input {
        display: flex;
        gap: 12px;
        margin-bottom: 24px;
        
        .custom-input {
          flex: 1;
        }
      }
      
      .recommended-topics {
        h4 {
          margin: 0 0 16px 0;
          font-size: 16px;
          font-weight: 500;
          color: #303133;
        }
        
        .topic-grid {
          display: grid;
          grid-template-columns: repeat(auto-fill, minmax(100px, 1fr));
          gap: 12px;
          
          .topic-btn {
            height: 36px;
            font-size: 14px;
            border-radius: 6px;
            min-width: 100px;
            padding: 0 12px;
            white-space: nowrap;
            text-align: center;
            display: flex;
            align-items: center;
            justify-content: center;
            
            &.el-button--primary {
              background-color: #409eff;
              border-color: #409eff;
              color: white;
            }
          }
        }
      }
    }
    
    .dialog-footer {
      display: flex;
      justify-content: flex-end;
      gap: 12px;
    }
  }
}
</style>
