import {
  IMAGE_FILE_FORMAT_TEXT,
  VIDEO_FILE_FORMAT_TEXT,
  isImageMaterial,
  isVideoMaterial
} from '@/constants/materialFormats'
import {
  PUBLISH_CONTENT_TYPE_IMAGE_TEXT,
  PUBLISH_CONTENT_TYPE_LABEL_BY_VALUE,
  PUBLISH_CONTENT_TYPE_VIDEO
} from '@/constants/publishPlatforms'

/**
 * 返回当前内容类型对应的上传区标题。
 */
export function getUploadSectionTitle(contentType) {
  return PUBLISH_CONTENT_TYPE_LABEL_BY_VALUE[contentType] || '素材'
}

/**
 * 返回当前内容类型对应的上传按钮文案。
 */
export function getUploadButtonText(contentType) {
  const label = PUBLISH_CONTENT_TYPE_LABEL_BY_VALUE[contentType] || '素材'
  return `上传${label}`
}

/**
 * 返回当前内容类型对应的本地上传 accept。
 */
export function getUploadAccept(contentType) {
  return contentType === PUBLISH_CONTENT_TYPE_IMAGE_TEXT ? 'image/*' : 'video/*'
}

/**
 * 返回当前内容类型对应的上传提示文案。
 */
export function getUploadTipText(contentType) {
  if (contentType === PUBLISH_CONTENT_TYPE_IMAGE_TEXT) {
    return `支持 ${IMAGE_FILE_FORMAT_TEXT} 图片格式，可一次选择多张图片组成一条图文。`
  }
  return `支持 ${VIDEO_FILE_FORMAT_TEXT} 视频格式，可一次选择多个视频。`
}

/**
 * 判断文件名是否兼容当前内容类型。
 */
export function isFilenameCompatibleWithContentType(filename, contentType) {
  if (contentType === PUBLISH_CONTENT_TYPE_IMAGE_TEXT) {
    return isImageMaterial(filename)
  }
  return isVideoMaterial(filename)
}

/**
 * 过滤掉与当前内容类型不兼容的已选素材。
 */
export function filterFilesByContentType(fileList, contentType) {
  return fileList.filter((file) => isFilenameCompatibleWithContentType(file.name, contentType))
}

/**
 * 过滤素材库列表，只保留当前内容类型允许的素材。
 */
export function filterMaterialRecordsByContentType(materials, contentType) {
  return materials.filter((material) => isFilenameCompatibleWithContentType(material.filename, contentType))
}

/**
 * 把上传接口回调对象转为发布中心内部统一素材结构。
 */
export function createPublishFileFromUpload(response, file, previewUrlBuilder) {
  const filePath = response.data.path || response.data.filepath || response.data
  const filename = filePath.split('/').pop()
  return {
    name: file.name,
    url: previewUrlBuilder(filename),
    path: filePath,
    size: file.size,
    type: file.type
  }
}

/**
 * 把素材库记录转为发布中心内部统一素材结构。
 */
export function createPublishFileFromMaterial(material, previewUrlBuilder) {
  return {
    name: material.filename,
    url: previewUrlBuilder(material.file_path.split('/').pop()),
    path: material.file_path,
    size: material.filesize * 1024 * 1024,
    type: isImageMaterial(material.filename) ? 'image/*' : 'video/*'
  }
}

/**
 * 重建用于展示的轻量文件列表，避免模板依赖完整上传对象。
 */
export function buildDisplayFileList(fileList) {
  return fileList.map((item) => ({
    name: item.name,
    url: item.url
  }))
}

/**
 * 返回当前内容类型缺少素材时的错误提示。
 */
export function getEmptyFileMessage(contentType) {
  return contentType === PUBLISH_CONTENT_TYPE_IMAGE_TEXT ? '请先上传图文图片' : '请先上传视频文件'
}

/**
 * 图文模式下，发布中心需要给正文输入框更明确的占位文案。
 */
export function getNotePlaceholder(platformName) {
  return `请输入${platformName}图文正文`
}

export {
  PUBLISH_CONTENT_TYPE_IMAGE_TEXT,
  PUBLISH_CONTENT_TYPE_VIDEO
}
