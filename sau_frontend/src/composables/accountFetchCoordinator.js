/**
 * 把快速加载接口返回的数据临时标记为“验证中”，避免旧状态误导用户。
 */
function buildPendingAccounts(accounts) {
  return accounts.map((account) => {
    const updatedAccount = [...account]
    updatedAccount[4] = -1
    return updatedAccount
  })
}

/**
 * 创建账号拉取协调器，保证只有最新一次校验请求有资格回写列表。
 */
export function createAccountFetchCoordinator({
  loadQuickAccounts = async () => ({ code: 200, data: [] }),
  loadValidatedAccounts,
  applyAccounts,
  setRefreshing,
  onValidatedSuccess = () => {},
  onValidatedFailure = () => {},
  onQuickFailure = () => {}
}) {
  let activeValidatedRequests = 0
  let latestValidatedRequestId = 0
  let hasAppliedValidatedResult = false

  /**
   * 快速获取账号列表，只在还没有校验结果时回写，避免被旧快照覆盖。
   */
  async function fetchQuickAccounts() {
    try {
      const res = await loadQuickAccounts()
      if (hasAppliedValidatedResult) {
        return { ignored: true }
      }

      if (res.code === 200 && res.data) {
        applyAccounts(buildPendingAccounts(res.data))
        return { applied: true }
      }

      onQuickFailure()
      return { applied: false }
    } catch (error) {
      onQuickFailure(error)
      return { applied: false, error }
    }
  }

  /**
   * 获取带校验的账号列表，`force` 用于新增账号成功后的强制追平。
   */
  async function fetchValidatedAccounts(options = {}) {
    const { silent = false, force = false } = options
    if (activeValidatedRequests > 0 && !force) {
      return { skipped: true }
    }

    const requestId = ++latestValidatedRequestId
    activeValidatedRequests += 1
    setRefreshing(true)

    try {
      const res = await loadValidatedAccounts()
      const isLatestRequest = requestId === latestValidatedRequestId

      if (!isLatestRequest) {
        return { ignored: true }
      }

      if (res.code === 200 && res.data) {
        hasAppliedValidatedResult = true
        applyAccounts(res.data)
        onValidatedSuccess({ silent })
        return { applied: true }
      }

      onValidatedFailure({ silent })
      return { applied: false }
    } catch (error) {
      if (requestId === latestValidatedRequestId) {
        onValidatedFailure({ silent, error })
      }
      return { applied: false, error }
    } finally {
      activeValidatedRequests = Math.max(0, activeValidatedRequests - 1)
      if (activeValidatedRequests === 0) {
        setRefreshing(false)
      }
    }
  }

  return {
    fetchQuickAccounts,
    fetchValidatedAccounts
  }
}
