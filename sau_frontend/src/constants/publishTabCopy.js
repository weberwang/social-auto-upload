import {
  copyPublishTabToPlatform,
  flattenPublishTabState,
  migrateLegacyPublishTab
} from './publishTabState.js'

/**
 * 为新建标签生成干净状态，复用统一状态模型保证平台专属字段结构一致。
 */
export function createEmptyPublishTab() {
  return flattenPublishTabState(migrateLegacyPublishTab({}, 0))
}

/**
 * 根据目标平台复制当前标签内容；旧导出保留给页面调用，实际规则下沉到统一状态模型。
 */
export function createCopiedPublishTab(sourceTab, targetPlatformKey, nextTabIndex) {
  return flattenPublishTabState(copyPublishTabToPlatform(sourceTab, targetPlatformKey, nextTabIndex))
}

/**
 * 按平台列表批量复制标签，默认跳过源标签当前平台，避免“复制全部平台”制造同平台重复项。
 */
export function createCopiedPublishTabsForPlatforms(
  sourceTab,
  targetPlatformKeys,
  nextTabStartIndex
) {
  const sourcePlatformKey = migrateLegacyPublishTab(sourceTab).platform.selectedPlatform
  const uniqueTargetPlatformKeys = [...new Set(targetPlatformKeys)]
    .filter((platformKey) => Number(platformKey) && Number(platformKey) !== sourcePlatformKey)

  return uniqueTargetPlatformKeys.map((platformKey, index) => (
    flattenPublishTabState(copyPublishTabToPlatform(sourceTab, platformKey, nextTabStartIndex + index))
  ))
}
