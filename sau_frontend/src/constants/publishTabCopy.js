import {
  buildPublishTabLabel,
  createDefaultPublishTab,
  PUBLISH_CONTENT_TYPE_IMAGE_TEXT,
  resolveSupportedContentType
} from './publishPlatforms.js'
import {
  buildDisplayFileList,
  filterFilesByContentType
} from './publishMaterials.js'

/**
 * 深拷贝发布中心表单对象，避免复制后的新标签与源标签共享引用。
 */
function clonePublishTabState(value) {
  try {
    return typeof structuredClone === 'function'
      ? structuredClone(value)
      : JSON.parse(JSON.stringify(value))
  } catch (error) {
    return JSON.parse(JSON.stringify(value))
  }
}

/**
 * 为新建标签生成干净的默认状态，统一复用默认模型的深拷贝策略。
 */
export function createEmptyPublishTab() {
  return clonePublishTabState(createDefaultPublishTab())
}

/**
 * 根据目标平台复制当前标签内容，只保留可跨平台复用且兼容的字段。
 */
export function createCopiedPublishTab(sourceTab, targetPlatformKey, nextTabIndex) {
  const defaultTab = createDefaultPublishTab()
  const safeSourceTab = sourceTab && typeof sourceTab === 'object'
    ? clonePublishTabState(sourceTab)
    : createEmptyPublishTab()
  const nextPlatformKey = Number(targetPlatformKey) || defaultTab.selectedPlatform
  const copiedTab = {
    ...defaultTab,
    name: `tab${nextTabIndex}`,
    label: buildPublishTabLabel(nextPlatformKey, []),
    fileList: Array.isArray(safeSourceTab.fileList) ? safeSourceTab.fileList : [],
    contentType: safeSourceTab.contentType || defaultTab.contentType,
    title: typeof safeSourceTab.title === 'string' ? safeSourceTab.title : defaultTab.title,
    noteContent: typeof safeSourceTab.noteContent === 'string'
      ? safeSourceTab.noteContent
      : defaultTab.noteContent,
    selectedTopics: Array.isArray(safeSourceTab.selectedTopics)
      ? safeSourceTab.selectedTopics
      : [],
    scheduleEnabled: Boolean(safeSourceTab.scheduleEnabled),
    videosPerDay: Number(safeSourceTab.videosPerDay) || defaultTab.videosPerDay,
    dailyTimes: Array.isArray(safeSourceTab.dailyTimes) && safeSourceTab.dailyTimes.length > 0
      ? safeSourceTab.dailyTimes
      : [...defaultTab.dailyTimes],
    startDays: Number.isInteger(safeSourceTab.startDays) ? safeSourceTab.startDays : defaultTab.startDays,
    publishStatus: null,
    publishing: false,
    isOriginal: Boolean(safeSourceTab.isOriginal),
    selectedPlatform: nextPlatformKey,
    selectedAccounts: []
  }

  copiedTab.contentType = resolveSupportedContentType(
    copiedTab.selectedPlatform,
    safeSourceTab.contentType || defaultTab.contentType
  )
  copiedTab.fileList = filterFilesByContentType(
    Array.isArray(safeSourceTab.fileList) ? safeSourceTab.fileList : [],
    copiedTab.contentType
  )
  copiedTab.displayFileList = buildDisplayFileList(copiedTab.fileList)

  // 目标平台不支持图文时，正文和图文素材必须一起回退，避免复制后形成脏数据。
  if (copiedTab.contentType !== PUBLISH_CONTENT_TYPE_IMAGE_TEXT) {
    copiedTab.noteContent = ''
  }

  // B站、抖音、视频号的专属字段只在各自链路中保留，跨平台复制时统一清空。
  if (
    copiedTab.selectedPlatform === 5
    && safeSourceTab.selectedPlatform === 5
    && copiedTab.contentType !== PUBLISH_CONTENT_TYPE_IMAGE_TEXT
  ) {
    copiedTab.description = typeof safeSourceTab.description === 'string'
      ? safeSourceTab.description
      : defaultTab.description
    copiedTab.bilibiliTid = Number.isInteger(safeSourceTab.bilibiliTid)
      ? safeSourceTab.bilibiliTid
      : defaultTab.bilibiliTid
  } else if (
    copiedTab.selectedPlatform !== 5
    || safeSourceTab.selectedPlatform !== 5
    || copiedTab.contentType === PUBLISH_CONTENT_TYPE_IMAGE_TEXT
  ) {
    copiedTab.description = ''
    copiedTab.bilibiliTid = null
  }
  if (
    copiedTab.selectedPlatform === 3
    && safeSourceTab.selectedPlatform === 3
    && copiedTab.contentType !== PUBLISH_CONTENT_TYPE_IMAGE_TEXT
  ) {
    copiedTab.productLink = typeof safeSourceTab.productLink === 'string'
      ? safeSourceTab.productLink
      : defaultTab.productLink
    copiedTab.productTitle = typeof safeSourceTab.productTitle === 'string'
      ? safeSourceTab.productTitle
      : defaultTab.productTitle
  } else if (
    copiedTab.selectedPlatform !== 3
    || safeSourceTab.selectedPlatform !== 3
    || copiedTab.contentType === PUBLISH_CONTENT_TYPE_IMAGE_TEXT
  ) {
    copiedTab.productLink = ''
    copiedTab.productTitle = ''
  }
  if (
    copiedTab.selectedPlatform === 2
    && safeSourceTab.selectedPlatform === 2
    && copiedTab.contentType !== PUBLISH_CONTENT_TYPE_IMAGE_TEXT
  ) {
    copiedTab.isDraft = Boolean(safeSourceTab.isDraft)
  } else if (
    copiedTab.selectedPlatform !== 2
    || safeSourceTab.selectedPlatform !== 2
    || copiedTab.contentType === PUBLISH_CONTENT_TYPE_IMAGE_TEXT
  ) {
    copiedTab.isDraft = false
  }

  return copiedTab
}

/**
 * 按平台列表批量复制标签，默认跳过源标签当前平台，避免“复制全部平台”制造同平台重复项。
 */
export function createCopiedPublishTabsForPlatforms(
  sourceTab,
  targetPlatformKeys,
  nextTabStartIndex
) {
  const sourcePlatformKey = Number(sourceTab?.selectedPlatform) || 0
  const uniqueTargetPlatformKeys = [...new Set(targetPlatformKeys)]
    .filter((platformKey) => Number(platformKey) && Number(platformKey) !== sourcePlatformKey)

  return uniqueTargetPlatformKeys.map((platformKey, index) => (
    createCopiedPublishTab(sourceTab, platformKey, nextTabStartIndex + index)
  ))
}
