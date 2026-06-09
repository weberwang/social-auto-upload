<template>
  <div class="xiaohongshu-video-enhancement">
    <h3>小红书配置</h3>
    <el-input
      v-model="thumbnailPathModel"
      type="text"
      maxlength="500"
      placeholder="请输入视频封面路径（可选）"
      class="xiaohongshu-thumbnail-path-input"
    />
    <el-input
      v-model="locationModel"
      type="text"
      maxlength="50"
      placeholder="请输入位置（可选）"
      class="xiaohongshu-location-input"
    />
  </div>
</template>

<script setup>
import { computed } from 'vue'

/**
 * 小红书视频增强字段当前先开放封面和位置，两者都能直接映射到现有主线 uploader 能力。
 */
const props = defineProps({
  thumbnailPath: {
    type: String,
    default: ''
  },
  location: {
    type: String,
    default: ''
  }
})

const emit = defineEmits([
  'update:thumbnailPath',
  'update:location'
])

const thumbnailPathModel = computed({
  get: () => props.thumbnailPath,
  set: (value) => emit('update:thumbnailPath', value)
})

const locationModel = computed({
  get: () => props.location,
  set: (value) => emit('update:location', value)
})
</script>
