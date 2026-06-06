import {
  createDefaultPublishTab,
  resolveSupportedContentType
} from '@/constants/publishPlatforms'
import {
  PUBLISH_CONTENT_TYPE_IMAGE_TEXT,
  buildDisplayFileList
} from '@/constants/publishMaterials'

const DEFAULT_DRAFT_VERSION = 1

/**
 * 深拷贝普通对象，避免把 Vue 响应式对象直接写入草稿快照。
 */
function clonePlainObject(value) {
  return JSON.parse(JSON.stringify(value))
}

/**
 * 生成默认草稿名称，方便用户快速保存当前发布工作区。
 */
export function buildDefaultDraftName() {
  const now = new Date()
  const month = String(now.getMonth() + 1).padStart(2, '0')
  const day = String(now.getDate()).padStart(2, '0')
  const hours = String(now.getHours()).padStart(2, '0')
  const minutes = String(now.getMinutes()).padStart(2, '0')
  return `发布草稿 ${month}-${day} ${hours}:${minutes}`
}

/**
 * 把单个 Tab 规整成可持久化的草稿对象，去掉运行态字段并补齐展示字段。
 */
export function serializePublishTab(tab) {
  const clonedTab = clonePlainObject(tab)
  return {
    ...clonedTab,
    publishStatus: null,
    publishing: false,
    displayFileList: buildDisplayFileList(clonedTab.fileList || [])
  }
}

/**
 * 把当前发布中心工作区转换为后端可持久化的草稿快照。
 */
export function buildPublishDraftWorkspace(tabs, activeTab, tabCounter) {
  return {
    version: DEFAULT_DRAFT_VERSION,
    activeTab,
    tabCounter,
    tabs: tabs.map((tab) => serializePublishTab(tab))
  }
}

/**
 * 把草稿里的单个 Tab 恢复为页面可直接使用的表单状态。
 */
export function restorePublishTab(rawTab, index) {
  const defaultTab = createDefaultPublishTab()
  const safeTab = rawTab && typeof rawTab === 'object' ? clonePlainObject(rawTab) : {}
  const restoredTab = {
    ...defaultTab,
    ...safeTab,
    name: safeTab.name || `tab${index + 1}`,
    label: safeTab.label || `发布${index + 1}`,
    publishStatus: null,
    publishing: false,
    selectedPlatform: Number(safeTab.selectedPlatform) || defaultTab.selectedPlatform
  }

  restoredTab.contentType = resolveSupportedContentType(
    restoredTab.selectedPlatform,
    restoredTab.contentType || defaultTab.contentType
  )
  restoredTab.fileList = Array.isArray(restoredTab.fileList) ? restoredTab.fileList : []
  restoredTab.displayFileList = buildDisplayFileList(restoredTab.fileList)
  restoredTab.selectedAccounts = Array.isArray(restoredTab.selectedAccounts)
    ? restoredTab.selectedAccounts
    : []
  restoredTab.selectedTopics = Array.isArray(restoredTab.selectedTopics)
    ? restoredTab.selectedTopics
    : []
  restoredTab.dailyTimes = Array.isArray(restoredTab.dailyTimes) && restoredTab.dailyTimes.length > 0
    ? restoredTab.dailyTimes
    : ['10:00']

  if (restoredTab.contentType !== PUBLISH_CONTENT_TYPE_IMAGE_TEXT) {
    restoredTab.noteContent = ''
  }

  return restoredTab
}

/**
 * 把后端草稿详情恢复为完整工作区，供发布中心一次性替换全部 Tab。
 */
export function restorePublishDraftWorkspace(workspace) {
  const safeWorkspace = workspace && typeof workspace === 'object' ? workspace : {}
  const rawTabs = Array.isArray(safeWorkspace.tabs) ? safeWorkspace.tabs : []
  const restoredTabs = rawTabs.length > 0
    ? rawTabs.map((tab, index) => restorePublishTab(tab, index))
    : [restorePublishTab({}, 0)]
  const tabCounter = Math.max(
    Number(safeWorkspace.tabCounter) || restoredTabs.length,
    restoredTabs.length,
  )
  const activeTab = restoredTabs.some((tab) => tab.name === safeWorkspace.activeTab)
    ? safeWorkspace.activeTab
    : restoredTabs[0].name

  return {
    tabs: restoredTabs,
    activeTab,
    tabCounter
  }
}
