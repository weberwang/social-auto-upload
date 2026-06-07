<template>
  <el-dialog
    v-model="dialogVisible"
    title="素材预览"
    width="60%"
    :top="'10vh'"
    @close="handleDialogClose"
  >
    <div class="preview-container" v-if="material">
      <div class="preview-meta">
        <div class="preview-meta__title">{{ material.filename }}</div>
        <div class="preview-meta__details">
          <span>类型：{{ getMaterialType(material.filename) }}</span>
          <span>大小：{{ material.filesize }} MB</span>
          <span v-if="material.upload_time">上传时间：{{ material.upload_time }}</span>
          <span v-if="material.remark">备注：{{ material.remark }}</span>
        </div>
      </div>
      <el-skeleton v-if="previewLoading" :rows="8" animated />
      <el-alert
        v-else-if="previewErrorMessage"
        :title="previewErrorMessage"
        type="warning"
        :closable="false"
        show-icon
      />
      <div v-else-if="previewKind === 'video'" class="video-preview">
        <video
          ref="previewVideoRef"
          controls
          autoplay
          playsinline
          preload="metadata"
          style="max-width: 100%; max-height: 60vh;"
        >
          <source :src="previewUrl" :type="previewMimeType">
          您的浏览器不支持视频播放
        </video>
      </div>
      <div v-else-if="previewKind === 'image'" class="image-preview">
        <img :src="previewUrl" :alt="material.filename" style="max-width: 100%; max-height: 60vh;" />
      </div>
      <div v-else-if="previewKind === 'audio'" class="audio-preview">
        <audio controls :src="previewUrl" :type="previewMimeType" style="width: 100%;" />
      </div>
      <div v-else-if="previewKind === 'document'" class="document-preview">
        <iframe :src="previewUrl" title="素材文档预览" class="document-preview__frame" />
      </div>
      <div v-else-if="previewKind === 'text'" class="text-preview">
        <pre>{{ textPreviewContent }}</pre>
      </div>
      <div v-else class="file-info">
        <p>当前格式暂不支持内联预览，请下载后查看。</p>
      </div>
      <div class="preview-actions">
        <el-button @click="openPreviewInNewTab">新窗口打开</el-button>
        <el-button type="primary" @click="downloadFile">下载文件</el-button>
      </div>
    </div>
  </el-dialog>
</template>

<script setup>
import { computed, nextTick, ref, watch } from 'vue'
import { materialApi } from '@/api/material'
import {
  getAudioMimeType,
  getMaterialPreviewKind,
  getMaterialType,
  getVideoMimeType
} from '@/constants/materialFormats'

const props = defineProps({
  modelValue: {
    type: Boolean,
    required: true
  },
  material: {
    type: Object,
    default: null
  }
})

const emit = defineEmits(['update:modelValue'])

const previewLoading = ref(false)
const textPreviewContent = ref('')
const previewErrorMessage = ref('')
const previewVideoRef = ref(null)

const dialogVisible = computed({
  get: () => props.modelValue,
  set: (value) => emit('update:modelValue', value)
})

/**
 * 当前素材的预览模式由共享格式规则统一推导。
 */
const previewKind = computed(() => (
  props.material ? getMaterialPreviewKind(props.material.filename) : 'unsupported'
))

/**
 * 统一暴露当前预览链接，避免模板重复拆文件路径。
 */
const previewUrl = computed(() => {
  if (!props.material) {
    return ''
  }
  const filename = props.material.file_path.split('/').pop()
  return materialApi.getMaterialPreviewUrl(filename)
})

/**
 * 根据素材类型选择媒体 MIME，确保视频和音频预览更稳定。
 */
const previewMimeType = computed(() => {
  if (!props.material) {
    return ''
  }

  switch (previewKind.value) {
    case 'video':
      return getVideoMimeType(props.material.filename)
    case 'audio':
      return getAudioMimeType(props.material.filename)
    default:
      return ''
  }
})

/**
 * 当弹窗打开或素材切换时加载预览，并在视频模式下尝试自动播放。
 */
const loadPreview = async () => {
  resetPreviewState()
  if (!dialogVisible.value || !props.material) {
    return
  }

  try {
    previewLoading.value = true
    if (previewKind.value === 'text') {
      const filename = props.material.file_path.split('/').pop()
      textPreviewContent.value = await materialApi.getMaterialTextPreview(filename)
    }
  } catch (error) {
    console.error('预览素材出错:', error)
    previewErrorMessage.value = error.message || '预览加载失败'
  } finally {
    previewLoading.value = false
  }

  if (previewKind.value === 'video') {
    await nextTick()
    const videoElement = previewVideoRef.value
    if (videoElement) {
      videoElement.currentTime = 0
      videoElement.muted = false
      videoElement.volume = 1
      try {
        await videoElement.play()
      } catch (error) {
        console.warn('视频自动播放失败，浏览器可能拦截了带声音自动播放，用户可手动点击播放:', error)
      }
    }
  }
}

watch(
  () => [dialogVisible.value, props.material?.file_path ?? '', props.material?.filename ?? ''],
  async () => {
    await loadPreview()
  }
)

/**
 * 关闭弹窗时统一清理预览态，避免残留旧素材内容。
 */
const resetPreviewState = () => {
  const videoElement = previewVideoRef.value
  if (videoElement) {
    videoElement.pause()
    videoElement.currentTime = 0
  }
  previewLoading.value = false
  textPreviewContent.value = ''
  previewErrorMessage.value = ''
  previewVideoRef.value = null
}

const handleDialogClose = () => {
  resetPreviewState()
  emit('update:modelValue', false)
}

const openPreviewInNewTab = () => {
  window.open(previewUrl.value, '_blank')
}

const downloadFile = () => {
  if (!props.material) {
    return
  }
  const url = materialApi.downloadMaterial(props.material.file_path)
  window.open(url, '_blank')
}
</script>

<style lang="scss" scoped>
@use '@/styles/variables.scss' as *;

.preview-container {
  display: flex;
  flex-direction: column;
  gap: 16px;
  padding: 0 20px;

  .preview-meta {
    width: 100%;
    display: flex;
    flex-direction: column;
    gap: 8px;

    .preview-meta__title {
      font-size: 16px;
      font-weight: 600;
      color: $text-primary;
      word-break: break-all;
    }

    .preview-meta__details {
      display: flex;
      flex-wrap: wrap;
      gap: 16px;
      font-size: 13px;
      color: $text-secondary;
    }
  }

  .video-preview,
  .image-preview,
  .audio-preview,
  .document-preview,
  .file-info {
    width: 100%;
    text-align: center;
  }

  .text-preview {
    width: 100%;
    max-height: 60vh;
    overflow: auto;
    padding: 16px;
    border-radius: 8px;
    background-color: #f6f8fa;
    border: 1px solid #e5e7eb;

    pre {
      margin: 0;
      font-size: 13px;
      line-height: 1.6;
      white-space: pre-wrap;
      word-break: break-word;
      color: $text-primary;
    }
  }

  .document-preview__frame {
    width: 100%;
    height: 60vh;
    border: 1px solid #dcdfe6;
    border-radius: 8px;
    background-color: #fff;
  }

  .preview-actions {
    width: 100%;
    display: flex;
    justify-content: flex-end;
    gap: 12px;
  }
}
</style>
