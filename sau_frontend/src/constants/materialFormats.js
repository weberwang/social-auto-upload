/**
 * 素材格式常量。
 * 统一维护前端可识别的视频/图片扩展名，避免素材管理和仪表盘各写一套判断逻辑。
 */
export const VIDEO_FILE_EXTENSIONS = ['.mp4', '.avi', '.mov', '.wmv', '.flv', '.mkv']

/**
 * 图文素材使用的图片扩展名。
 */
export const IMAGE_FILE_EXTENSIONS = ['.jpg', '.jpeg', '.png', '.gif', '.bmp', '.webp']

/**
 * 可直接文本预览的素材扩展名。
 */
export const TEXT_FILE_EXTENSIONS = ['.txt', '.json', '.md', '.csv', '.log']

/**
 * 浏览器可内嵌预览的文档扩展名。
 */
export const DOCUMENT_FILE_EXTENSIONS = ['.pdf']

/**
 * 浏览器可直接播放的音频扩展名。
 */
export const AUDIO_FILE_EXTENSIONS = ['.mp3', '.wav', '.ogg', '.m4a']

/**
 * 素材上传提示里使用的视频格式文案。
 */
export const VIDEO_FILE_FORMAT_TEXT = 'MP4 / AVI / MOV / WMV / FLV / MKV'

/**
 * 素材上传提示里使用的图片格式文案。
 */
export const IMAGE_FILE_FORMAT_TEXT = 'JPG / JPEG / PNG / GIF / BMP / WEBP'

/**
 * 判断文件名是否属于视频素材。
 */
export function isVideoMaterial(filename) {
  return VIDEO_FILE_EXTENSIONS.some((extension) => filename.toLowerCase().endsWith(extension))
}

/**
 * 判断文件名是否属于图片素材。
 */
export function isImageMaterial(filename) {
  return IMAGE_FILE_EXTENSIONS.some((extension) => filename.toLowerCase().endsWith(extension))
}

/**
 * 判断文件名是否属于文本预览素材。
 */
export function isTextMaterial(filename) {
  return TEXT_FILE_EXTENSIONS.some((extension) => filename.toLowerCase().endsWith(extension))
}

/**
 * 判断文件名是否属于浏览器文档预览素材。
 */
export function isDocumentMaterial(filename) {
  return DOCUMENT_FILE_EXTENSIONS.some((extension) => filename.toLowerCase().endsWith(extension))
}

/**
 * 判断文件名是否属于音频素材。
 */
export function isAudioMaterial(filename) {
  return AUDIO_FILE_EXTENSIONS.some((extension) => filename.toLowerCase().endsWith(extension))
}

/**
 * 返回素材的展示类型，供列表标签和统计卡片复用。
 */
export function getMaterialType(filename) {
  if (isVideoMaterial(filename)) {
    return '视频'
  }
  if (isImageMaterial(filename)) {
    return '图片'
  }
  return '其他'
}

/**
 * 返回素材类型对应的标签颜色，保持不同页面展示一致。
 */
export function getMaterialTypeTag(filename) {
  return {
    视频: 'success',
    图片: 'warning',
    其他: 'info'
  }[getMaterialType(filename)] || 'info'
}

/**
 * 返回视频预览使用的 MIME，避免所有视频都被错误标记成 mp4。
 */
export function getVideoMimeType(filename) {
  const lowerCaseFilename = filename.toLowerCase()
  if (lowerCaseFilename.endsWith('.mov')) {
    return 'video/quicktime'
  }
  if (lowerCaseFilename.endsWith('.avi')) {
    return 'video/x-msvideo'
  }
  if (lowerCaseFilename.endsWith('.wmv')) {
    return 'video/x-ms-wmv'
  }
  if (lowerCaseFilename.endsWith('.flv')) {
    return 'video/x-flv'
  }
  if (lowerCaseFilename.endsWith('.mkv')) {
    return 'video/x-matroska'
  }
  return 'video/mp4'
}

/**
 * 返回音频预览使用的 MIME。
 */
export function getAudioMimeType(filename) {
  const lowerCaseFilename = filename.toLowerCase()
  if (lowerCaseFilename.endsWith('.wav')) {
    return 'audio/wav'
  }
  if (lowerCaseFilename.endsWith('.ogg')) {
    return 'audio/ogg'
  }
  if (lowerCaseFilename.endsWith('.m4a')) {
    return 'audio/mp4'
  }
  return 'audio/mpeg'
}

/**
 * 根据文件名推导素材预览模式，供素材管理弹窗统一分发。
 */
export function getMaterialPreviewKind(filename) {
  if (isVideoMaterial(filename)) {
    return 'video'
  }
  if (isImageMaterial(filename)) {
    return 'image'
  }
  if (isAudioMaterial(filename)) {
    return 'audio'
  }
  if (isDocumentMaterial(filename)) {
    return 'document'
  }
  if (isTextMaterial(filename)) {
    return 'text'
  }
  return 'unsupported'
}
