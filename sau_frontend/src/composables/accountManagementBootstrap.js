/**
 * 决定账号管理页在挂载时是否需要自动拉取数据。
 */
export async function bootstrapAccountManagementPage({
  isFirstVisit,
  hasCachedAccounts,
  fetchAccountsQuick,
  validateAllAccountsInBackground
}) {
  // 首次进入必须做一次完整同步，保证用户第一次看到的是最新状态。
  if (isFirstVisit) {
    await fetchAccountsQuick()
    validateAllAccountsInBackground()
    return
  }

  // 再次进入时优先复用内存中的账号列表，避免切页就触发平台校验。
  if (hasCachedAccounts) {
    return
  }

  // 只有缓存为空时才补一次本地列表，避免空白页，但不自动访问平台。
  await fetchAccountsQuick()
}
