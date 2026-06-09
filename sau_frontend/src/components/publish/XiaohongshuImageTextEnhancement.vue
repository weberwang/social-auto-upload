<template>
  <div class="xiaohongshu-image-text-enhancement">
    <h3>小红书配置</h3>
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
 * 小红书图文当前先开放位置字段，直接复用主线基类已具备的位置设置能力。
 */
const props = defineProps({
  location: {
    type: String,
    default: ''
  }
})

const emit = defineEmits([
  'update:location'
])

const locationModel = computed({
  get: () => props.location,
  set: (value) => emit('update:location', value)
})
</script>
