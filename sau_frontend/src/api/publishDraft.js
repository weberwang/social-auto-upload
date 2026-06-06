import { http } from '@/utils/request'

/**
 * 发布中心草稿 API。
 * 独立封装保存、列表、详情、删除能力，避免页面直接拼接口细节。
 */
export const publishDraftApi = {
  /**
   * 保存或覆盖发布中心草稿。
   */
  saveDraft(data) {
    return http.post('/savePublishDraft', data)
  },

  /**
   * 获取草稿列表。
   */
  getDrafts() {
    return http.get('/getPublishDrafts')
  },

  /**
   * 获取单个草稿详情。
   */
  getDraft(id) {
    return http.get('/getPublishDraft', { id })
  },

  /**
   * 删除指定草稿。
   */
  deleteDraft(id) {
    return http.get('/deletePublishDraft', { id })
  }
}
