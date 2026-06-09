<template>
  <div class="douyin-image-text-enhancement">
    <h3>抖音配置</h3>
    <el-input
      v-model="locationModel"
      type="text"
      maxlength="50"
      placeholder="请输入地理位置（可选）"
      class="douyin-location-input"
    />
    <el-input
      v-model="selfDeclarationModel"
      type="text"
      maxlength="50"
      placeholder="请输入自主声明文案"
      class="douyin-self-declaration-input"
    />
  </div>
</template>

<script setup>
import { computed } from 'vue'

/**
 * 抖音图文增强字段当前先开放位置和自主声明，和主线图文 uploader 的可落地能力保持一致。
 */
const props = defineProps({
  location: {
    type: String,
    default: ''
  },
  selfDeclaration: {
    type: String,
    default: ''
  }
})

const emit = defineEmits([
  'update:location',
  'update:selfDeclaration'
])

const locationModel = computed({
  get: () => props.location,
  set: (value) => emit('update:location', value)
})

const selfDeclarationModel = computed({
  get: () => props.selfDeclaration,
  set: (value) => emit('update:selfDeclaration', value)
})
</script>
