import { computed, ref } from 'vue'
import { ElMessage, ElMessageBox } from 'element-plus'
import { publishDraftApi } from '@/api/publishDraft'
import {
  buildDefaultDraftName,
  buildPublishDraftWorkspace
} from '@/constants/publishDrafts'

/**
 * 管理发布中心草稿的请求状态与交互流程。
 * 这里把保存、加载、删除都收口，避免页面脚本继续堆满接口细节。
 */
export function usePublishDrafts(options) {
  const draftDialogVisible = ref(false)
  const draftLoading = ref(false)
  const draftItems = ref([])
  const currentDraftMeta = ref(null)

  /**
   * 当前已绑定草稿名称，供草稿弹窗展示“这次保存会覆盖谁”。
   */
  const currentDraftName = computed(() => currentDraftMeta.value?.name || '')

  /**
   * Element Plus 的弹窗取消会以动作字符串抛出，这里统一识别并静默处理。
   */
  const isDialogCanceled = (error) => error === 'cancel' || error === 'close'

  /**
   * 拉取草稿列表，保证加载弹窗里的数据始终是最新的。
   */
  const refreshDrafts = async () => {
    draftLoading.value = true
    try {
      const response = await publishDraftApi.getDrafts()
      draftItems.value = Array.isArray(response.data) ? response.data : []
    } finally {
      draftLoading.value = false
    }
  }

  /**
   * 打开草稿列表前先刷新一次，避免用户看到过期数据。
   */
  const openDraftDialog = async () => {
    draftDialogVisible.value = true
    await refreshDrafts()
  }

  /**
   * 把当前工作区保存成草稿；如果已加载过草稿，则默认覆盖原草稿。
   */
  const saveDraft = async () => {
    try {
      const defaultName = currentDraftMeta.value?.name || buildDefaultDraftName()
      const { value } = await ElMessageBox.prompt('请输入草稿名称', '保存草稿', {
        confirmButtonText: '保存',
        cancelButtonText: '取消',
        inputValue: defaultName,
        inputPattern: /\S+/,
        inputErrorMessage: '草稿名称不能为空'
      })
      const payload = {
        name: value.trim(),
        workspace: buildPublishDraftWorkspace(
          options.getTabs(),
          options.getActiveTab(),
          options.getTabCounter(),
        )
      }
      const isUpdatingCurrentDraft = Boolean(currentDraftMeta.value?.id)

      if (currentDraftMeta.value?.id) {
        payload.id = currentDraftMeta.value.id
      }

      const response = await publishDraftApi.saveDraft(payload)
      currentDraftMeta.value = {
        id: response.data.id,
        name: response.data.name
      }
      ElMessage.success(isUpdatingCurrentDraft ? '草稿已更新' : '草稿已保存')
      if (draftDialogVisible.value) {
        await refreshDrafts()
      }
    } catch (error) {
      if (!isDialogCanceled(error)) {
        throw error
      }
    }
  }

  /**
   * 加载草稿后用父组件提供的回填函数替换整个发布中心工作区。
   */
  const loadDraft = async (draft) => {
    const response = await publishDraftApi.getDraft(draft.id)
    options.applyWorkspace(response.data.workspace)
    currentDraftMeta.value = {
      id: response.data.id,
      name: response.data.name
    }
    draftDialogVisible.value = false
    ElMessage.success(`已加载草稿：${response.data.name}`)
  }

  /**
   * 删除草稿前增加确认，避免误删用户正在维护的发布方案。
   */
  const removeDraft = async (draft) => {
    try {
      await ElMessageBox.confirm(`确定删除草稿“${draft.name}”吗？`, '删除草稿', {
        confirmButtonText: '删除',
        cancelButtonText: '取消',
        type: 'warning'
      })
      await publishDraftApi.deleteDraft(draft.id)
      if (currentDraftMeta.value?.id === draft.id) {
        currentDraftMeta.value = null
      }
      ElMessage.success('草稿已删除')
      await refreshDrafts()
    } catch (error) {
      if (!isDialogCanceled(error)) {
        throw error
      }
    }
  }

  return {
    currentDraftName,
    draftDialogVisible,
    draftItems,
    draftLoading,
    openDraftDialog,
    refreshDrafts,
    removeDraft,
    saveDraft,
    loadDraft
  }
}
