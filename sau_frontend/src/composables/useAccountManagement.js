import { computed, onBeforeUnmount, onMounted, reactive, ref } from 'vue'
import { ElMessage, ElMessageBox } from 'element-plus'

import { accountApi } from '../api/account.js'
import { useAccountStore } from '../stores/account.js'
import { useAppStore } from '../stores/app.js'
import { http } from '../utils/request.js'
import { bootstrapAccountManagementPage } from './accountManagementBootstrap.js'
import { createAccountFetchCoordinator } from './accountFetchCoordinator.js'
import {
  ACCOUNT_PLATFORM_SSE_LOGIN_SUPPORTED_LABELS,
  ACCOUNT_PLATFORM_TAG_TYPE_MAP,
  ACCOUNT_PLATFORM_TYPE_BY_LABEL
} from '../constants/accountPlatforms.js'

/**
 * 账号管理页面状态与交互的组合式封装。
 */
export function useAccountManagement() {
  const accountStore = useAccountStore()
  const appStore = useAppStore()

  const activeTab = ref('all')
  const searchKeyword = ref('')
  const dialogVisible = ref(false)
  const dialogType = ref('add')
  const accountFormRef = ref(null)
  const sseConnecting = ref(false)
  const qrCodeData = ref('')
  const loginStatus = ref('')
  const loginErrorMessage = ref('')
  const accountForm = reactive({
    id: null,
    name: '',
    platform: '',
    status: '正常'
  })
  const rules = {
    platform: [{ required: true, message: '请选择平台', trigger: 'change' }],
    name: [{ required: true, message: '请输入账号名称', trigger: 'blur' }]
  }

  let eventSource = null

  /**
   * 统一处理手动刷新、自动同步、后台校验，避免多个请求互相覆盖。
   */
  const accountFetchCoordinator = createAccountFetchCoordinator({
    loadQuickAccounts: () => accountApi.getAccounts(),
    loadValidatedAccounts: () => accountApi.getValidAccounts(),
    applyAccounts: (accounts) => {
      accountStore.setAccounts(accounts)
    },
    setRefreshing: (status) => {
      appStore.setAccountRefreshing(status)
    },
    onValidatedSuccess: ({ silent }) => {
      if (!silent) {
        ElMessage.success('账号数据获取成功')
      }

      if (appStore.isFirstTimeAccountManagement) {
        appStore.setAccountManagementVisited()
      }
    },
    onValidatedFailure: ({ silent, error } = {}) => {
      if (error) {
        console.error('获取账号数据失败:', error)
      }

      if (!silent) {
        ElMessage.error('获取账号数据失败')
      }
    },
    onQuickFailure: (error) => {
      if (error) {
        console.error('快速获取账号数据失败:', error)
      }
    }
  })

  /**
   * 快速获取账号数据，优先让用户看到列表骨架数据。
   */
  async function fetchAccountsQuick() {
    await accountFetchCoordinator.fetchQuickAccounts()
  }

  /**
   * 获取账号数据并校验 cookie，支持静默刷新与强制追平。
   */
  async function fetchAccounts(options = {}) {
    return accountFetchCoordinator.fetchValidatedAccounts(options)
  }

  /**
   * 把慢校验延后到下一个事件循环，避免首次进入页面时卡住界面。
   */
  async function validateAllAccountsInBackground() {
    setTimeout(() => {
      fetchAccounts({ silent: true, force: true })
    }, 0)
  }

  /**
   * 返回平台标签样式。
   */
  function getPlatformTagType(platform) {
    return ACCOUNT_PLATFORM_TAG_TYPE_MAP[platform] || 'info'
  }

  /**
   * 只有异常账号允许点击触发重新登录，防止正常账号误触发扫码流程。
   */
  function isStatusClickable(status) {
    return status === '异常'
  }

  /**
   * 返回账号状态标签样式。
   */
  function getStatusTagType(status) {
    if (status === '验证中') {
      return 'info'
    }

    if (status === '正常') {
      return 'success'
    }

    return 'danger'
  }

  /**
   * 平台扫码登录能力由统一常量维护，避免页面与后端支持集不一致。
   */
  function supportsSseLogin(platform) {
    return ACCOUNT_PLATFORM_SSE_LOGIN_SUPPORTED_LABELS.has(platform)
  }

  /**
   * 状态标签点击入口，只把异常状态转到重新登录流程。
   */
  function handleStatusClick(row) {
    if (isStatusClickable(row.status)) {
      handleReLogin(row)
    }
  }

  /**
   * 搜索逻辑由计算属性承接，保留该方法用于模板事件绑定语义。
   */
  function handleSearch() {}

  /**
   * 打开新增账号弹窗，并清空上一次扫码残留状态。
   */
  function handleAddAccount() {
    dialogType.value = 'add'
    Object.assign(accountForm, {
      id: null,
      name: '',
      platform: '',
      status: '正常'
    })
    sseConnecting.value = false
    qrCodeData.value = ''
    loginStatus.value = ''
    loginErrorMessage.value = ''
    dialogVisible.value = true
  }

  /**
   * 打开编辑账号弹窗，仅修改账号名称与平台展示信息。
   */
  function handleEdit(row) {
    dialogType.value = 'edit'
    Object.assign(accountForm, {
      id: row.id,
      name: row.name,
      platform: row.platform,
      status: row.status
    })
    dialogVisible.value = true
  }

  /**
   * 删除账号并同步清理前端状态，避免页面和数据库内容不一致。
   */
  function handleDelete(row) {
    ElMessageBox.confirm(`确定要删除账号 ${row.name} 吗？`, '警告', {
      confirmButtonText: '确定',
      cancelButtonText: '取消',
      type: 'warning'
    })
      .then(async () => {
        try {
          const response = await accountApi.deleteAccount(row.id)
          if (response.code === 200) {
            accountStore.deleteAccount(row.id)
            ElMessage({
              type: 'success',
              message: '删除成功'
            })
          } else {
            ElMessage.error(response.msg || '删除失败')
          }
        } catch (error) {
          console.error('删除账号失败:', error)
          ElMessage.error('删除账号失败')
        }
      })
      .catch(() => {})
  }

  /**
   * 下载账号对应的 cookie 文件，便于跨环境迁移或手动备份。
   */
  function handleDownloadCookie(row) {
    const baseUrl = import.meta.env.VITE_API_BASE_URL || 'http://localhost:5409'
    const downloadUrl = `${baseUrl}/downloadCookie?filePath=${encodeURIComponent(row.filePath)}`
    const link = document.createElement('a')
    link.href = downloadUrl
    link.download = `${row.name}_cookie.json`
    link.target = '_blank'
    link.style.display = 'none'
    document.body.appendChild(link)
    link.click()
    document.body.removeChild(link)
  }

  /**
   * 上传替换 cookie 后强制追平账号列表，避免旧请求把新状态覆盖回去。
   */
  function handleUploadCookie(row) {
    const input = document.createElement('input')
    input.type = 'file'
    input.accept = '.json'
    input.style.display = 'none'
    document.body.appendChild(input)

    input.onchange = async (event) => {
      const file = event.target.files[0]
      if (!file) {
        document.body.removeChild(input)
        return
      }

      if (!file.name.endsWith('.json')) {
        ElMessage.error('请选择JSON格式的Cookie文件')
        document.body.removeChild(input)
        return
      }

      try {
        const formData = new FormData()
        formData.append('file', file)
        formData.append('id', row.id)
        formData.append('platform', row.platform)
        await http.upload('/uploadCookie', formData)
        ElMessage.success('Cookie文件上传成功')
        await fetchAccounts({ silent: true, force: true })
      } catch (error) {
        ElMessage.error('Cookie文件上传失败')
      } finally {
        document.body.removeChild(input)
      }
    }

    input.click()
  }

  /**
   * 异常账号重新登录时沿用原账号信息，并立即进入扫码流程。
   */
  function handleReLogin(row) {
    dialogType.value = 'edit'
    Object.assign(accountForm, {
      id: row.id,
      name: row.name,
      platform: row.platform,
      status: row.status
    })
    sseConnecting.value = false
    qrCodeData.value = ''
    loginStatus.value = ''
    loginErrorMessage.value = ''
    dialogVisible.value = true

    setTimeout(() => {
      connectSSE(row.platform, row.name)
    }, 300)
  }

  /**
   * 生成默认头像，避免没有平台头像时列表视觉完全空白。
   */
  function getDefaultAvatar(name) {
    return `https://ui-avatars.com/api/?name=${encodeURIComponent(name)}&background=random`
  }

  /**
   * 关闭当前 SSE 连接，避免多次扫码流程并发写入同一弹窗状态。
   */
  function closeSSEConnection() {
    if (eventSource) {
      eventSource.close()
      eventSource = null
    }
  }

  /**
   * 建立登录 SSE 连接，负责接收二维码与登录结果。
   */
  function connectSSE(platform, name) {
    if (!supportsSseLogin(platform)) {
      ElMessage.error('当前平台暂不支持扫码登录')
      return
    }

    closeSSEConnection()
    sseConnecting.value = true
    qrCodeData.value = ''
    loginStatus.value = ''
    loginErrorMessage.value = ''

    const type = String(ACCOUNT_PLATFORM_TYPE_BY_LABEL[platform] || 1)
    const baseUrl = import.meta.env.VITE_API_BASE_URL || 'http://localhost:5409'
    const url = `${baseUrl}/login?type=${type}&id=${encodeURIComponent(name)}`

    eventSource = new EventSource(url)

    eventSource.onmessage = (event) => {
      const data = event.data

      if (!qrCodeData.value && data.length > 100) {
        try {
          qrCodeData.value = data.startsWith('data:image')
            ? data
            : `data:image/png;base64,${data}`
        } catch (error) {
          console.error('处理二维码数据失败:', error)
        }
        return
      }

      if (data.startsWith('ERROR:')) {
        loginErrorMessage.value = data.slice('ERROR:'.length).trim()
        return
      }

      if (data !== '200' && data !== '500') {
        return
      }

      loginStatus.value = data
      if (data === '200') {
        setTimeout(() => {
          closeSSEConnection()

          setTimeout(async () => {
            dialogVisible.value = false
            sseConnecting.value = false
            ElMessage.success(dialogType.value === 'edit' ? '重新登录成功' : '账号添加成功')

            // 登录成功后的自动同步必须强制走最新请求，否则会被旧校验结果回滚掉。
            const syncingMessage = ElMessage({
              type: 'info',
              message: '正在同步账号信息...',
              duration: 0
            })

            try {
              await fetchAccounts({ silent: true, force: true })
              syncingMessage.close()
              ElMessage.success('账号信息已更新')
            } catch (error) {
              syncingMessage.close()
              ElMessage.error('账号信息同步失败，请稍后重试')
            }
          }, 1000)
        }, 1000)
        return
      }

      closeSSEConnection()
      setTimeout(() => {
        sseConnecting.value = false
        qrCodeData.value = ''
        loginStatus.value = ''
        if (loginErrorMessage.value) {
          ElMessage.error(loginErrorMessage.value)
        }
      }, 2000)
    }

    eventSource.onerror = (error) => {
      console.error('SSE连接错误:', error)
      ElMessage.error('连接服务器失败，请稍后再试')
      closeSSEConnection()
      sseConnecting.value = false
    }
  }

  /**
   * 提交账号表单；新增走扫码，编辑走普通更新。
   */
  function submitAccountForm() {
    accountFormRef.value.validate(async (valid) => {
      if (!valid) {
        return false
      }

      if (dialogType.value === 'add') {
        if (!supportsSseLogin(accountForm.platform)) {
          ElMessage.error('当前平台暂不支持扫码登录')
          return false
        }

        connectSSE(accountForm.platform, accountForm.name)
        return true
      }

      try {
        const type = ACCOUNT_PLATFORM_TYPE_BY_LABEL[accountForm.platform] || 1
        const res = await accountApi.updateAccount({
          id: accountForm.id,
          type,
          userName: accountForm.name
        })

        if (res.code === 200) {
          accountStore.updateAccount(accountForm.id, {
            id: accountForm.id,
            name: accountForm.name,
            platform: accountForm.platform,
            status: accountForm.status
          })
          ElMessage.success('更新成功')
          dialogVisible.value = false
          await fetchAccounts({ silent: true, force: true })
        } else {
          ElMessage.error(res.msg || '更新账号失败')
        }
      } catch (error) {
        console.error('更新账号失败:', error)
        ElMessage.error('更新账号失败')
      }

      return true
    })
  }

  const filteredAccounts = computed(() => {
    if (!searchKeyword.value) {
      return accountStore.accounts
    }

    return accountStore.accounts.filter((account) => account.name.includes(searchKeyword.value))
  })

  const filteredKuaishouAccounts = computed(() => {
    return filteredAccounts.value.filter((account) => account.platform === '快手')
  })

  const filteredDouyinAccounts = computed(() => {
    return filteredAccounts.value.filter((account) => account.platform === '抖音')
  })

  const filteredChannelsAccounts = computed(() => {
    return filteredAccounts.value.filter((account) => account.platform === '视频号')
  })

  const filteredXiaohongshuAccounts = computed(() => {
    return filteredAccounts.value.filter((account) => account.platform === '小红书')
  })

  /**
   * B 站当前只补展示链路与基础编辑能力，便于和 CLI 主线共存。
   */
  const filteredBilibiliAccounts = computed(() => {
    return filteredAccounts.value.filter((account) => account.platform === 'B站')
  })

  /**
   * 首次进入页面先快速出列表，再后台静默校验，兼顾感知速度与准确性。
   */
  onMounted(() => {
    bootstrapAccountManagementPage({
      isFirstVisit: appStore.isFirstTimeAccountManagement,
      hasCachedAccounts: accountStore.accounts.length > 0,
      fetchAccountsQuick,
      validateAllAccountsInBackground
    })
  })

  /**
   * 页面销毁时主动断开 SSE，避免离页后仍然占用浏览器连接。
   */
  onBeforeUnmount(() => {
    closeSSEConnection()
  })

  return {
    accountForm,
    accountFormRef,
    activeTab,
    appStore,
    dialogType,
    dialogVisible,
    fetchAccounts,
    filteredAccounts,
    filteredChannelsAccounts,
    filteredBilibiliAccounts,
    filteredDouyinAccounts,
    filteredKuaishouAccounts,
    filteredXiaohongshuAccounts,
    getDefaultAvatar,
    getPlatformTagType,
    getStatusTagType,
    handleAddAccount,
    handleDelete,
    handleDownloadCookie,
    handleEdit,
    handleReLogin,
    handleSearch,
    handleStatusClick,
    handleUploadCookie,
    isStatusClickable,
    loginStatus,
    loginErrorMessage,
    qrCodeData,
    rules,
    searchKeyword,
    sseConnecting,
    submitAccountForm
  }
}
