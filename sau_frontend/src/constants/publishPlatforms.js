/**
 * 发布中心平台配置。
 * 这里统一维护平台编号、名称和账号平台映射，避免超长视图文件继续堆平台分支。
 */
import { IMAGE_FILE_FORMAT_TEXT, VIDEO_FILE_FORMAT_TEXT } from './materialFormats.js'

export const PUBLISH_CONTENT_TYPE_VIDEO = 'video'
export const PUBLISH_CONTENT_TYPE_IMAGE_TEXT = 'image_text'

/**
 * 发布中心内容类型文案映射。
 */
export const PUBLISH_CONTENT_TYPE_LABEL_BY_VALUE = {
  [PUBLISH_CONTENT_TYPE_VIDEO]: '视频',
  [PUBLISH_CONTENT_TYPE_IMAGE_TEXT]: '图文'
}

export const PUBLISH_PLATFORM_OPTIONS = [
  {
    key: 3,
    name: '抖音',
    supportedMaterialTypes: ['视频', '图文'],
    supportedContentTypes: [PUBLISH_CONTENT_TYPE_VIDEO, PUBLISH_CONTENT_TYPE_IMAGE_TEXT],
    materialSupportDescription: `视频支持 ${VIDEO_FILE_FORMAT_TEXT}；图文图片支持 ${IMAGE_FILE_FORMAT_TEXT}。`
  },
  {
    key: 4,
    name: '快手',
    supportedMaterialTypes: ['视频', '图文'],
    supportedContentTypes: [PUBLISH_CONTENT_TYPE_VIDEO, PUBLISH_CONTENT_TYPE_IMAGE_TEXT],
    materialSupportDescription: `视频支持 ${VIDEO_FILE_FORMAT_TEXT}；图文图片支持 ${IMAGE_FILE_FORMAT_TEXT}。`
  },
  {
    key: 2,
    name: '视频号',
    supportedMaterialTypes: ['视频'],
    supportedContentTypes: [PUBLISH_CONTENT_TYPE_VIDEO],
    materialSupportDescription: `当前主线仅支持视频素材发布，视频格式支持 ${VIDEO_FILE_FORMAT_TEXT}。`
  },
  {
    key: 1,
    name: '小红书',
    supportedMaterialTypes: ['视频', '图文'],
    supportedContentTypes: [PUBLISH_CONTENT_TYPE_VIDEO, PUBLISH_CONTENT_TYPE_IMAGE_TEXT],
    materialSupportDescription: `视频支持 ${VIDEO_FILE_FORMAT_TEXT}；图文图片支持 ${IMAGE_FILE_FORMAT_TEXT}。`
  },
  {
    key: 5,
    name: 'B站',
    supportedMaterialTypes: ['视频'],
    supportedContentTypes: [PUBLISH_CONTENT_TYPE_VIDEO],
    materialSupportDescription: `当前主线仅支持视频素材发布，视频格式支持 ${VIDEO_FILE_FORMAT_TEXT}。`
  },
  {
    key: 6,
    name: '微信公众号',
    supportedMaterialTypes: ['图文'],
    supportedContentTypes: [PUBLISH_CONTENT_TYPE_IMAGE_TEXT],
    materialSupportDescription: `当前主线支持图文草稿发布，图片格式支持 ${IMAGE_FILE_FORMAT_TEXT}。`
  }
]

/**
 * 发布平台编号到账号平台名称的映射。
 */
export const PUBLISH_ACCOUNT_PLATFORM_BY_KEY = {
  1: '小红书',
  2: '视频号',
  3: '抖音',
  4: '快手',
  5: 'B站',
  6: '微信公众号'
}

/**
 * 把已选账号 ID 转成页签标题需要的展示名称，账号列表未就绪时回退到原始 ID。
 */
export function resolvePublishTabAccountNames(selectedAccountIds, accounts) {
  return selectedAccountIds.map((accountId) => {
    const matchedAccount = accounts.find((account) => String(account.id) === String(accountId))
    return matchedAccount?.name || String(accountId)
  })
}

/**
 * 统一生成发布页签标题，格式固定为“账号 + 平台”，多账号时收敛成首个账号加数量。
 */
export function buildPublishTabLabel(platformKey, selectedAccountIds = [], accounts = []) {
  const platformName = getPublishPlatformOption(platformKey)?.name || '未选平台'
  const accountNames = resolvePublishTabAccountNames(selectedAccountIds, accounts)

  if (accountNames.length === 0) {
    return `未选账号·${platformName}`
  }

  if (accountNames.length === 1) {
    return `${accountNames[0]}·${platformName}`
  }

  return `${accountNames[0]}等${accountNames.length}个·${platformName}`
}

/**
 * 创建发布 Tab 的初始状态。
 * B 站的简介和分区单独作为平台专属字段，避免污染其他平台逻辑。
 */
export function createDefaultPublishTab() {
  return {
    name: 'tab1',
    label: buildPublishTabLabel(1, []),
    fileList: [],
    displayFileList: [],
    selectedAccounts: [],
    selectedPlatform: 1,
    contentType: PUBLISH_CONTENT_TYPE_VIDEO,
    title: '',
    description: '',
    noteContent: '',
    bilibiliTid: null,
    productLink: '',
    productTitle: '',
    selectedTopics: [],
    scheduleEnabled: false,
    videosPerDay: 1,
    dailyTimes: ['10:00'],
    startDays: 0,
    publishStatus: null,
    publishing: false,
    isDraft: false,
    isOriginal: false
  }
}

/**
 * 根据平台编号返回平台配置，供发布中心统一读取能力矩阵。
 */
export function getPublishPlatformOption(platformKey) {
  return PUBLISH_PLATFORM_OPTIONS.find((platform) => platform.key === platformKey) || null
}

/**
 * 返回某个平台允许的内容类型列表。
 */
export function getSupportedContentTypesForPlatform(platformKey) {
  return getPublishPlatformOption(platformKey)?.supportedContentTypes || [PUBLISH_CONTENT_TYPE_VIDEO]
}

/**
 * 判断当前平台是否支持指定内容类型。
 */
export function isContentTypeSupportedForPlatform(platformKey, contentType) {
  return getSupportedContentTypesForPlatform(platformKey).includes(contentType)
}

/**
 * 为平台选择默认内容类型，优先保留当前值，否则回退到平台支持的第一项。
 */
export function resolveSupportedContentType(platformKey, contentType) {
  if (isContentTypeSupportedForPlatform(platformKey, contentType)) {
    return contentType
  }
  return getSupportedContentTypesForPlatform(platformKey)[0] || PUBLISH_CONTENT_TYPE_VIDEO
}

/**
 * 返回当前平台下可选的账号列表。
 */
export function getAvailableAccountsForPlatform(accounts, platformKey) {
  const platformName = PUBLISH_ACCOUNT_PLATFORM_BY_KEY[platformKey]
  return platformName ? accounts.filter((account) => account.platform === platformName) : []
}

/**
 * 多账号场景下保留当前平台全部合法账号；如果一个都没有，再回填该平台第一个账号。
 */
export function getDefaultSelectedAccountIdsForPlatform(accounts, selectedAccountIds, platformKey) {
  const availableAccounts = getAvailableAccountsForPlatform(accounts, platformKey)
  const availableAccountIds = new Set(availableAccounts.map((account) => account.id))
  const matchedAccountIds = selectedAccountIds.filter((accountId) => availableAccountIds.has(accountId))

  if (matchedAccountIds.length > 0) {
    return matchedAccountIds
  }

  if (availableAccounts.length > 0) {
    return [availableAccounts[0].id]
  }

  return []
}

/**
 * 过滤掉不属于当前平台的已选账号，避免用户先选账号再切平台后残留脏数据。
 */
export function filterAccountIdsForPlatform(accounts, selectedAccountIds, platformKey) {
  const availableIds = new Set(
    getAvailableAccountsForPlatform(accounts, platformKey).map((account) => account.id)
  )
  return selectedAccountIds.filter((accountId) => availableIds.has(accountId))
}

/**
 * 返回当前平台下不匹配的账号名称列表，发布前用于给出明确错误提示。
 */
export function getMismatchedAccountNamesForPlatform(accounts, selectedAccountIds, platformKey) {
  const availableIds = new Set(
    getAvailableAccountsForPlatform(accounts, platformKey).map((account) => account.id)
  )
  return selectedAccountIds
    .map((accountId) => accounts.find((account) => account.id === accountId))
    .filter((account) => account && !availableIds.has(account.id))
    .map((account) => account.name)
}

/**
 * 把当前 Tab 的表单状态组装成历史 Web 发布接口请求。
 * 同时补充 B 站专属字段和账号名称列表，便于后端桥接到主线能力。
 */
export function buildPublishPayload(tab, accounts) {
  return {
    type: tab.selectedPlatform,
    contentType: tab.contentType,
    title: tab.title,
    description: tab.description.trim(),
    noteContent: tab.noteContent.trim(),
    tid: tab.bilibiliTid,
    tags: tab.selectedTopics,
    fileList: tab.fileList.map((file) => file.path),
    accountList: tab.selectedAccounts.map((accountId) => {
      const account = accounts.find((item) => item.id === accountId)
      return account ? account.filePath : accountId
    }),
    accountNameList: tab.selectedAccounts.map((accountId) => {
      const account = accounts.find((item) => item.id === accountId)
      return account ? account.name : String(accountId)
    }),
    enableTimer: tab.scheduleEnabled ? 1 : 0,
    videosPerDay: tab.scheduleEnabled ? tab.videosPerDay || 1 : 1,
    dailyTimes: tab.scheduleEnabled ? tab.dailyTimes || ['10:00'] : ['10:00'],
    startDays: tab.scheduleEnabled ? tab.startDays || 0 : 0,
    category: tab.isOriginal ? 1 : 0,
    productLink: tab.productLink.trim() || '',
    productTitle: tab.productTitle.trim() || '',
    isDraft: tab.isDraft
  }
}
