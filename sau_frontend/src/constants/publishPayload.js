import { migrateLegacyPublishTab } from './publishTabState.js'

/**
 * 把统一状态模型映射为历史 `/postVideo` 兼容请求，同时保留新的基础字段/平台字段结构。
 */
export function buildPublishPayloadFromState(tab, accounts) {
  const normalizedTab = migrateLegacyPublishTab(tab)

  return {
    type: normalizedTab.platform.selectedPlatform,
    contentType: normalizedTab.platform.contentType,
    baseFields: {
      title: normalizedTab.baseFields.title.trim(),
      description: normalizedTab.baseFields.description.trim(),
      noteContent: normalizedTab.baseFields.noteContent.trim(),
      tags: normalizedTab.baseFields.topics,
      enableTimer: normalizedTab.baseFields.scheduleEnabled ? 1 : 0,
      videosPerDay: normalizedTab.baseFields.scheduleEnabled ? normalizedTab.baseFields.videosPerDay || 1 : 1,
      dailyTimes: normalizedTab.baseFields.scheduleEnabled
        ? normalizedTab.baseFields.dailyTimes || ['10:00']
        : ['10:00'],
      startDays: normalizedTab.baseFields.scheduleEnabled ? normalizedTab.baseFields.startDays || 0 : 0
    },
    platformFields: normalizedTab.platformFields,
    fileList: normalizedTab.materials.fileList.map((file) => file.path),
    accountList: normalizedTab.accounts.selectedAccountIds.map((accountId) => {
      const account = accounts.find((item) => item.id === accountId)
      return account ? account.filePath : accountId
    }),
    accountNameList: normalizedTab.accounts.selectedAccountIds.map((accountId) => {
      const account = accounts.find((item) => item.id === accountId)
      return account ? account.name : String(accountId)
    })
  }
}
