import {
  buildPublishTabLabel,
  PUBLISH_CONTENT_TYPE_IMAGE_TEXT,
  PUBLISH_CONTENT_TYPE_VIDEO,
  resolveSupportedContentType
} from './publishPlatforms.js'
import {
  buildDisplayFileList,
  filterFilesByContentType
} from './publishMaterials.js'

const DEFAULT_SELECTED_PLATFORM = 1
const BILIBILI_PLATFORM_KEY = 5
const DOUYIN_PLATFORM_KEY = 3
const TENCENT_PLATFORM_KEY = 2

/**
 * 深拷贝发布 Tab 状态，避免默认数组、平台字段和复制来源共享引用。
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
 * 把输入收敛为有效整数；平台编号、页签编号和分区 ID 都通过这里兜底。
 */
function resolveInteger(value, fallback) {
  if (value === null || value === undefined || value === '') {
    return fallback
  }

  const numberValue = Number(value)
  return Number.isInteger(numberValue) ? numberValue : fallback
}

/**
 * 生成平台专属字段默认值，跨平台复制时用它清空 B站、抖音、视频号的私有数据。
 */
function createDefaultPlatformFields(overrides = {}) {
  return {
    douyin: {
      productLink: typeof overrides.douyin?.productLink === 'string' ? overrides.douyin.productLink : '',
      productTitle: typeof overrides.douyin?.productTitle === 'string' ? overrides.douyin.productTitle : ''
    },
    kuaishou: {
      ...(overrides.kuaishou && typeof overrides.kuaishou === 'object' ? overrides.kuaishou : {})
    },
    xiaohongshu: {
      ...(overrides.xiaohongshu && typeof overrides.xiaohongshu === 'object' ? overrides.xiaohongshu : {})
    },
    tencent: {
      shortTitle: typeof overrides.tencent?.shortTitle === 'string' ? overrides.tencent.shortTitle : '',
      collectionName: typeof overrides.tencent?.collectionName === 'string' ? overrides.tencent.collectionName : '',
      declareOriginal: Boolean(overrides.tencent?.declareOriginal),
      originalType: typeof overrides.tencent?.originalType === 'string' ? overrides.tencent.originalType : '',
      contentDeclaration: typeof overrides.tencent?.contentDeclaration === 'string' ? overrides.tencent.contentDeclaration : '',
      noteCoverPath: typeof overrides.tencent?.noteCoverPath === 'string' ? overrides.tencent.noteCoverPath : '',
      isDraft: Boolean(overrides.tencent?.isDraft)
    },
    bilibili: {
      description: typeof overrides.bilibili?.description === 'string' ? overrides.bilibili.description : '',
      tid: resolveInteger(overrides.bilibili?.tid ?? overrides.bilibili?.bilibiliTid, null)
    }
  }
}

/**
 * 根据平台和内容类型选择增强组件名称，避免主页面继续堆平台分支。
 */
export function getPlatformEnhancementComponentName(platformKey, contentType) {
  if (platformKey === TENCENT_PLATFORM_KEY) {
    return contentType === PUBLISH_CONTENT_TYPE_IMAGE_TEXT
      ? 'TencentImageTextEnhancement'
      : 'TencentVideoEnhancement'
  }
  if (platformKey === BILIBILI_PLATFORM_KEY && contentType !== PUBLISH_CONTENT_TYPE_IMAGE_TEXT) {
    return 'BilibiliPublishFields'
  }
  return null
}

/**
 * 生成统一的 Tab 默认状态；页面仍可通过 flatten 取得旧字段桥接。
 */
export function createDefaultPublishTabState(overrides = {}) {
  const selectedPlatform = resolveInteger(overrides.platform?.selectedPlatform, DEFAULT_SELECTED_PLATFORM)
  const selectedAccountIds = Array.isArray(overrides.accounts?.selectedAccountIds)
    ? clonePublishTabState(overrides.accounts.selectedAccountIds)
    : []

  return {
    meta: {
      name: typeof overrides.meta?.name === 'string' && overrides.meta.name ? overrides.meta.name : 'tab1',
      label: typeof overrides.meta?.label === 'string' && overrides.meta.label
        ? overrides.meta.label
        : buildPublishTabLabel(selectedPlatform, selectedAccountIds)
    },
    platform: {
      selectedPlatform,
      contentType: typeof overrides.platform?.contentType === 'string' && overrides.platform.contentType
        ? overrides.platform.contentType
        : PUBLISH_CONTENT_TYPE_VIDEO
    },
    materials: {
      fileList: Array.isArray(overrides.materials?.fileList)
        ? clonePublishTabState(overrides.materials.fileList)
        : [],
      displayFileList: Array.isArray(overrides.materials?.displayFileList)
        ? clonePublishTabState(overrides.materials.displayFileList)
        : []
    },
    accounts: {
      selectedAccountIds
    },
    baseFields: {
      title: typeof overrides.baseFields?.title === 'string' ? overrides.baseFields.title : '',
      // 简介曾经在顶层混用，这里只保留通用槽位，平台简介迁移到 platformFields。
      description: typeof overrides.baseFields?.description === 'string' ? overrides.baseFields.description : '',
      noteContent: typeof overrides.baseFields?.noteContent === 'string' ? overrides.baseFields.noteContent : '',
      topics: Array.isArray(overrides.baseFields?.topics)
        ? clonePublishTabState(overrides.baseFields.topics)
        : [],
      scheduleEnabled: Boolean(overrides.baseFields?.scheduleEnabled),
      videosPerDay: Number(overrides.baseFields?.videosPerDay) || 1,
      dailyTimes: Array.isArray(overrides.baseFields?.dailyTimes) && overrides.baseFields.dailyTimes.length > 0
        ? clonePublishTabState(overrides.baseFields.dailyTimes)
        : ['10:00'],
      startDays: resolveInteger(overrides.baseFields?.startDays, 0)
    },
    platformFields: createDefaultPlatformFields(overrides.platformFields || {}),
    status: {
      publishStatus: overrides.status?.publishStatus ?? null,
      publishing: Boolean(overrides.status?.publishing),
      isOriginal: Boolean(overrides.status?.isOriginal)
    }
  }
}

/**
 * 判断对象是否已经是统一状态模型，避免重复迁移时丢失平台分区字段。
 */
function isPublishTabState(value) {
  return Boolean(
    value
      && typeof value === 'object'
      && value.meta
      && value.platform
      && value.platformFields
  )
}

/**
 * 从旧平铺字段、state 包装或统一模型中提取平台专属字段。
 */
function resolvePlatformFields(safeTab) {
  const stateSource = safeTab.state && typeof safeTab.state === 'object' ? safeTab.state : safeTab
  const platformFields = stateSource.platformFields && typeof stateSource.platformFields === 'object'
    ? stateSource.platformFields
    : {}

  return createDefaultPlatformFields({
    ...platformFields,
    bilibili: {
      ...(platformFields.bilibili || {}),
      description: typeof platformFields.bilibili?.description === 'string'
        ? platformFields.bilibili.description
        : (typeof safeTab.description === 'string' ? safeTab.description : ''),
      tid: platformFields.bilibili?.tid ?? platformFields.bilibili?.bilibiliTid ?? safeTab.bilibiliTid
    },
    douyin: {
      ...(platformFields.douyin || {}),
      productLink: typeof platformFields.douyin?.productLink === 'string'
        ? platformFields.douyin.productLink
        : (typeof safeTab.productLink === 'string' ? safeTab.productLink : ''),
      productTitle: typeof platformFields.douyin?.productTitle === 'string'
        ? platformFields.douyin.productTitle
        : (typeof safeTab.productTitle === 'string' ? safeTab.productTitle : '')
    },
    tencent: {
      ...(platformFields.tencent || {}),
      shortTitle: typeof platformFields.tencent?.shortTitle === 'string'
        ? platformFields.tencent.shortTitle
        : (typeof safeTab.shortTitle === 'string' ? safeTab.shortTitle : ''),
      collectionName: typeof platformFields.tencent?.collectionName === 'string'
        ? platformFields.tencent.collectionName
        : (typeof safeTab.collectionName === 'string' ? safeTab.collectionName : ''),
      declareOriginal: typeof platformFields.tencent?.declareOriginal === 'boolean'
        ? platformFields.tencent.declareOriginal
        : Boolean(safeTab.declareOriginal),
      originalType: typeof platformFields.tencent?.originalType === 'string'
        ? platformFields.tencent.originalType
        : (typeof safeTab.originalType === 'string' ? safeTab.originalType : ''),
      contentDeclaration: typeof platformFields.tencent?.contentDeclaration === 'string'
        ? platformFields.tencent.contentDeclaration
        : (typeof safeTab.contentDeclaration === 'string' ? safeTab.contentDeclaration : ''),
      noteCoverPath: typeof platformFields.tencent?.noteCoverPath === 'string'
        ? platformFields.tencent.noteCoverPath
        : (typeof safeTab.noteCoverPath === 'string' ? safeTab.noteCoverPath : ''),
      isDraft: typeof platformFields.tencent?.isDraft === 'boolean'
        ? platformFields.tencent.isDraft
        : Boolean(safeTab.isDraft)
    }
  })
}

/**
 * 把任意来源 Tab 归一化为统一状态模型，不直接处理内容类型兼容和运行态清理。
 */
export function normalizePublishTabState(rawTab, index = 0) {
  const safeTab = rawTab && typeof rawTab === 'object' ? rawTab : {}
  const stateSource = safeTab.state && typeof safeTab.state === 'object' ? safeTab.state : safeTab
  const selectedPlatform = resolveInteger(
    stateSource.platform?.selectedPlatform ?? safeTab.selectedPlatform,
    DEFAULT_SELECTED_PLATFORM
  )
  const selectedAccountIds = Array.isArray(stateSource.accounts?.selectedAccountIds)
    ? stateSource.accounts.selectedAccountIds
    : (Array.isArray(safeTab.selectedAccounts) ? safeTab.selectedAccounts : [])

  return createDefaultPublishTabState({
    meta: {
      name: typeof stateSource.meta?.name === 'string' && stateSource.meta.name
        ? stateSource.meta.name
        : (typeof safeTab.name === 'string' && safeTab.name ? safeTab.name : `tab${index + 1}`),
      label: typeof stateSource.meta?.label === 'string' && stateSource.meta.label
        ? stateSource.meta.label
        : (typeof safeTab.label === 'string' && safeTab.label
          ? safeTab.label
          : buildPublishTabLabel(selectedPlatform, selectedAccountIds))
    },
    platform: {
      selectedPlatform,
      contentType: stateSource.platform?.contentType || safeTab.contentType || PUBLISH_CONTENT_TYPE_VIDEO
    },
    materials: {
      fileList: Array.isArray(stateSource.materials?.fileList)
        ? stateSource.materials.fileList
        : (Array.isArray(safeTab.fileList) ? safeTab.fileList : []),
      displayFileList: Array.isArray(stateSource.materials?.displayFileList)
        ? stateSource.materials.displayFileList
        : (Array.isArray(safeTab.displayFileList) ? safeTab.displayFileList : [])
    },
    accounts: {
      selectedAccountIds
    },
    baseFields: {
      title: typeof stateSource.baseFields?.title === 'string'
        ? stateSource.baseFields.title
        : (typeof safeTab.title === 'string' ? safeTab.title : ''),
      description: typeof stateSource.baseFields?.description === 'string'
        ? stateSource.baseFields.description
        : '',
      noteContent: typeof stateSource.baseFields?.noteContent === 'string'
        ? stateSource.baseFields.noteContent
        : (typeof safeTab.noteContent === 'string' ? safeTab.noteContent : ''),
      topics: Array.isArray(stateSource.baseFields?.topics)
        ? stateSource.baseFields.topics
        : (Array.isArray(safeTab.selectedTopics) ? safeTab.selectedTopics : []),
      scheduleEnabled: typeof stateSource.baseFields?.scheduleEnabled === 'boolean'
        ? stateSource.baseFields.scheduleEnabled
        : Boolean(safeTab.scheduleEnabled),
      videosPerDay: Number(stateSource.baseFields?.videosPerDay) || Number(safeTab.videosPerDay) || 1,
      dailyTimes: Array.isArray(stateSource.baseFields?.dailyTimes) && stateSource.baseFields.dailyTimes.length > 0
        ? stateSource.baseFields.dailyTimes
        : (Array.isArray(safeTab.dailyTimes) && safeTab.dailyTimes.length > 0 ? safeTab.dailyTimes : ['10:00']),
      startDays: resolveInteger(stateSource.baseFields?.startDays ?? safeTab.startDays, 0)
    },
    platformFields: resolvePlatformFields(safeTab),
    status: {
      publishStatus: stateSource.status?.publishStatus ?? safeTab.publishStatus ?? null,
      publishing: typeof stateSource.status?.publishing === 'boolean'
        ? stateSource.status.publishing
        : Boolean(safeTab.publishing),
      isOriginal: typeof stateSource.status?.isOriginal === 'boolean'
        ? stateSource.status.isOriginal
        : Boolean(safeTab.isOriginal)
    }
  })
}

/**
 * 把统一状态拍平成现有发布页仍在读取的字段，并附带 platformFields 供新逻辑使用。
 */
export function flattenPublishTabState(state) {
  const normalizedState = isPublishTabState(state) ? state : normalizePublishTabState(state)
  const selectedTopics = clonePublishTabState(normalizedState.baseFields.topics)
  const fileList = clonePublishTabState(normalizedState.materials.fileList)
  const displayFileList = Array.isArray(normalizedState.materials.displayFileList)
    && normalizedState.materials.displayFileList.length > 0
    ? clonePublishTabState(normalizedState.materials.displayFileList)
    : buildDisplayFileList(fileList)

  return {
    ...clonePublishTabState(normalizedState),
    state: clonePublishTabState(normalizedState),
    name: normalizedState.meta.name,
    label: normalizedState.meta.label,
    selectedPlatform: normalizedState.platform.selectedPlatform,
    selectedAccounts: clonePublishTabState(normalizedState.accounts.selectedAccountIds),
    contentType: normalizedState.platform.contentType,
    title: normalizedState.baseFields.title,
    description: normalizedState.platformFields.bilibili.description,
    noteContent: normalizedState.baseFields.noteContent,
    bilibiliTid: normalizedState.platformFields.bilibili.tid,
    productLink: normalizedState.platformFields.douyin.productLink,
    productTitle: normalizedState.platformFields.douyin.productTitle,
    selectedTopics,
    fileList,
    displayFileList,
    scheduleEnabled: normalizedState.baseFields.scheduleEnabled,
    videosPerDay: normalizedState.baseFields.videosPerDay,
    dailyTimes: clonePublishTabState(normalizedState.baseFields.dailyTimes),
    startDays: normalizedState.baseFields.startDays,
    publishStatus: normalizedState.status.publishStatus,
    publishing: normalizedState.status.publishing,
    shortTitle: normalizedState.platformFields.tencent.shortTitle,
    collectionName: normalizedState.platformFields.tencent.collectionName,
    declareOriginal: normalizedState.platformFields.tencent.declareOriginal,
    originalType: normalizedState.platformFields.tencent.originalType,
    contentDeclaration: normalizedState.platformFields.tencent.contentDeclaration,
    noteCoverPath: normalizedState.platformFields.tencent.noteCoverPath,
    isDraft: normalizedState.platformFields.tencent.isDraft,
    isOriginal: normalizedState.status.isOriginal
  }
}

/**
 * 恢复旧草稿时统一处理运行态清理、内容类型回退和 B站简介迁移。
 */
export function migrateLegacyPublishTab(rawTab, index = 0) {
  const normalizedState = normalizePublishTabState(rawTab, index)
  const selectedPlatform = normalizedState.platform.selectedPlatform
  const contentType = resolveSupportedContentType(selectedPlatform, normalizedState.platform.contentType)
  const fileList = filterFilesByContentType(normalizedState.materials.fileList, contentType)
  const migratedState = createDefaultPublishTabState({
    ...normalizedState,
    meta: {
      ...normalizedState.meta,
      label: buildPublishTabLabel(selectedPlatform, normalizedState.accounts.selectedAccountIds)
    },
    platform: {
      ...normalizedState.platform,
      contentType
    },
    materials: {
      fileList,
      displayFileList: buildDisplayFileList(fileList)
    },
    baseFields: {
      ...normalizedState.baseFields,
      // 视频模式不保留图文正文，避免恢复旧草稿后提交不兼容内容。
      noteContent: contentType === PUBLISH_CONTENT_TYPE_IMAGE_TEXT
        ? normalizedState.baseFields.noteContent
        : ''
    },
    status: {
      ...normalizedState.status,
      publishStatus: null,
      publishing: false
    }
  })

  return migratedState
}

/**
 * 复制 Tab 到目标平台，只保留通用字段，并按目标平台清理专属字段。
 */
export function copyPublishTabToPlatform(sourceTab, targetPlatformKey, nextTabIndex) {
  const sourceState = normalizePublishTabState(sourceTab)
  const selectedPlatform = resolveInteger(targetPlatformKey, DEFAULT_SELECTED_PLATFORM)
  const contentType = resolveSupportedContentType(selectedPlatform, sourceState.platform.contentType)
  const fileList = filterFilesByContentType(sourceState.materials.fileList, contentType)
  const preservesPlatformFields = sourceState.platform.selectedPlatform === selectedPlatform
    && contentType !== PUBLISH_CONTENT_TYPE_IMAGE_TEXT

  const platformFields = createDefaultPlatformFields()
  if (preservesPlatformFields && selectedPlatform === BILIBILI_PLATFORM_KEY) {
    platformFields.bilibili = clonePublishTabState(sourceState.platformFields.bilibili)
  }
  if (preservesPlatformFields && selectedPlatform === DOUYIN_PLATFORM_KEY) {
    platformFields.douyin = clonePublishTabState(sourceState.platformFields.douyin)
  }
  if (preservesPlatformFields && selectedPlatform === TENCENT_PLATFORM_KEY) {
    platformFields.tencent = clonePublishTabState(sourceState.platformFields.tencent)
  }

  return createDefaultPublishTabState({
    meta: {
      name: `tab${nextTabIndex}`,
      label: buildPublishTabLabel(selectedPlatform, [])
    },
    platform: {
      selectedPlatform,
      contentType
    },
    materials: {
      fileList,
      displayFileList: buildDisplayFileList(fileList)
    },
    accounts: {
      selectedAccountIds: []
    },
    baseFields: {
      title: sourceState.baseFields.title,
      description: sourceState.baseFields.description,
      noteContent: contentType === PUBLISH_CONTENT_TYPE_IMAGE_TEXT
        ? sourceState.baseFields.noteContent
        : '',
      topics: sourceState.baseFields.topics,
      scheduleEnabled: sourceState.baseFields.scheduleEnabled,
      videosPerDay: sourceState.baseFields.videosPerDay,
      dailyTimes: sourceState.baseFields.dailyTimes,
      startDays: sourceState.baseFields.startDays
    },
    platformFields,
    status: {
      publishStatus: null,
      publishing: false,
      isOriginal: sourceState.status.isOriginal
    }
  })
}
