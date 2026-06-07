/**
 * 把素材管理接口返回的记录规范化为共享预览对象。
 */
export function createPreviewItemFromMaterial(material) {
  return {
    filename: material.filename,
    file_path: material.file_path,
    filesize: material.filesize,
    upload_time: material.upload_time,
    remark: material.remark || ''
  }
}

/**
 * 把发布中心已选素材规范化为共享预览对象。
 * 发布中心内部文件大小以字节保存，这里统一换算为素材管理展示使用的 MB。
 */
export function createPreviewItemFromPublishFile(file) {
  return {
    filename: file.name,
    file_path: file.path,
    filesize: Number((file.size / (1024 * 1024)).toFixed(2)),
    upload_time: '',
    remark: file.remark || ''
  }
}
