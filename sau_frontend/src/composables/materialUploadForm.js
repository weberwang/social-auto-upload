/**
 * 同步当前上传文件的备注映射。
 * 该函数只保留仍然存在的文件备注，并为新文件补空串，避免删除文件后残留脏状态。
 */
export function syncMaterialRemarks(files, previousRemarks = {}) {
  const nextRemarks = {}

  for (const file of files) {
    nextRemarks[file.uid] = previousRemarks[file.uid] || ''
  }

  return nextRemarks
}

/**
 * 构造素材上传表单。
 * 上传接口改为只接收原始文件和备注，避免前端继续透传“自定义文件名”这一已下线能力。
 */
export function buildMaterialUploadFormData({ file, remark = '' }) {
  const formData = new FormData()
  formData.append('file', file.raw)

  const normalizedRemark = remark.trim()
  if (normalizedRemark) {
    formData.append('remark', normalizedRemark)
  }

  return formData
}
