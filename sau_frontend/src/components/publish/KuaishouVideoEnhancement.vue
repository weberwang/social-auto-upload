<template>
  <div class="kuaishou-video-enhancement">
    <h3>快手配置</h3>
    <el-input
      v-model="thumbnailPathModel"
      type="text"
      maxlength="500"
      placeholder="请输入自定义封面素材路径（可选）"
      class="kuaishou-thumbnail-path-input"
    />
  </div>
</template>

<script setup>
import { computed } from 'vue'

/**
 * 快手视频增强字段当前先开放自定义封面路径，直接复用主线 uploader 已支持的 thumbnail_path 能力。
 */
const props = defineProps({
  thumbnailPath: {
    type: String,
    default: ''
  }
})

const emit = defineEmits([
  'update:thumbnailPath'
])

const thumbnailPathModel = computed({
  get: () => props.thumbnailPath,
  set: (value) => emit('update:thumbnailPath', value)
})
</script>
