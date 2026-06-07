import {
  IMAGE_FILE_FORMAT_TEXT,
  isImageMaterial,
  isVideoMaterial,
  VIDEO_FILE_FORMAT_TEXT
} from './materialFormats.js'
import {
  getPublishPlatformOption,
  getSupportedContentTypesForPlatform,
  PUBLISH_CONTENT_TYPE_IMAGE_TEXT,
  PUBLISH_CONTENT_TYPE_VIDEO
} from './publishPlatforms.js'

/**
 * 发布中心主入口统一使用素材概念，避免视频/图文入口文案割裂。
 */
export function getUploadSectionTitle(contentType) {
  return '素材'
}

/**
 * 发布中心主入口直接进入素材选择，不再暴露“上传视频”这种内容类型绑定文案。
 */
export function getUploadButtonText(contentType) {
  return '选择素材'
}

/**
 * 本地上传时按内容类型限制可选文件，避免图文页误选视频。
 */
export function getUploadAccept(contentType) {
  return contentType === PUBLISH_CONTENT_TYPE_IMAGE_TEXT ? 'image/*' : 'video/*'
}

/**
 * 上传提示需要明确告诉用户当前内容类型支持什么素材。
 */
export function getUploadTipText(contentType) {
  if (contentType === PUBLISH_CONTENT_TYPE_IMAGE_TEXT) {
    return `支持 ${IMAGE_FILE_FORMAT_TEXT} 图片格式，可一次选择多张图片组成一条图文。`
  }
  return `支持 ${VIDEO_FILE_FORMAT_TEXT} 视频格式，可一次选择多个视频。`
}

/**
 * 发布中心素材弹窗需要展示全部素材，并根据平台能力决定图片是否可选。
 */
export function buildPublishMaterialSelectionRows(materials, platformKey) {
  const supportedContentTypes = getSupportedContentTypesForPlatform(platformKey)
  const supportsImageText = supportedContentTypes.includes(PUBLISH_CONTENT_TYPE_IMAGE_TEXT)
  const platformName = getPublishPlatformOption(platformKey)?.name || '当前平台'

  return materials.map((material) => ({
    ...material,
    ...resolveMaterialSelectionCapability(material.filename, supportsImageText, platformName)
  }))
}

/**
 * 视频始终可选；图片是否可选取决于平台是否支持图文发布。
 */
function resolveMaterialSelectionCapability(filename, supportsImageText, platformName) {
  if (isVideoMaterial(filename)) {
    return {
      compatible: true,
      selectionContentType: PUBLISH_CONTENT_TYPE_VIDEO,
      compatibilityMessage: '视频素材可选。'
    }
  }

  if (isImageMaterial(filename)) {
    if (supportsImageText) {
      return {
        compatible: true,
        selectionContentType: PUBLISH_CONTENT_TYPE_IMAGE_TEXT,
        compatibilityMessage: '图片素材可选，选择后将按图文发布。'
      }
    }

    return {
      compatible: false,
      selectionContentType: null,
      compatibilityMessage: `${platformName}当前不支持图文发布，图片素材不可选。`
    }
  }

  return {
    compatible: false,
    selectionContentType: null,
    compatibilityMessage: '当前仅支持视频和图片素材。'
  }
}

/**
 * 当素材库完全为空时，给出直接上传的兜底提示。
 */
export function getMaterialLibraryEmptyState(materials, contentType) {
  if (materials.length === 0) {
    return {
      description: '素材库暂无素材，请先上传素材。',
      showUploadAction: true
    }
  }

  return {
    description: '',
    showUploadAction: false
  }
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
 * 把本地上传返回结果转成发布中心统一素材结构，保持后续发布逻辑只消费一种数据形态。
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
 * 重建用于展示的轻量文件列表，避免模板依赖完整上传对象。
 */
export function buildDisplayFileList(fileList) {
  return fileList.map((item) => ({
    name: item.name,
    url: item.url
  }))
}

/**
 * 表格勾选事件可能反复回写同一组选中项，这里统一做集合比较，避免前后端状态同步进入死循环。
 */
export function areSelectedMaterialIdsEqual(previousIds, nextIds) {
  if (previousIds.length !== nextIds.length) {
    return false
  }

  const previousIdSet = new Set(previousIds)
  return nextIds.every((id) => previousIdSet.has(id))
}

/**
 * 发布前统一提示用户先补齐素材，避免继续暴露旧的“上传视频”措辞。
 */
export function getEmptyFileMessage(contentType) {
  return '请先选择素材'
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
