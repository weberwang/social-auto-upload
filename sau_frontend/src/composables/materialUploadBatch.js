/**
 * 汇总本次素材批量上传结果。
 * 只有全部文件都成功上传时才关闭弹窗，失败场景保留现场便于用户查看并重试。
 */
export function summarizeMaterialUploadResults(results) {
  const totalCount = results.length
  const successCount = results.filter((item) => item.status === 'success').length
  const failureCount = totalCount - successCount

  return {
    totalCount,
    successCount,
    failureCount,
    shouldCloseDialog: totalCount > 0 && failureCount === 0
  }
}
