<template>
  <div class="tencent-image-text-enhancement">
    <h3>视频号图文配置</h3>
    <el-input
      v-model="collectionNameModel"
      type="text"
      maxlength="50"
      placeholder="请输入合集名称"
      class="tencent-collection-input"
    />
    <el-input
      v-model="originalTypeModel"
      type="text"
      maxlength="50"
      placeholder="请输入原创类型"
      class="tencent-original-type-input"
    />
    <el-input
      v-model="contentDeclarationModel"
      type="text"
      maxlength="100"
      placeholder="请输入内容声明"
      class="tencent-content-declaration-input"
    />
    <el-checkbox v-model="declareOriginalModel" label="声明原创" />
    <el-checkbox v-model="isDraftModel" label="仅保存草稿(用手机发布)" />
  </div>
</template>

<script setup>
import { computed } from 'vue'

/**
 * 视频号图文增强组件只暴露首阶段已决定展示的字段，避免提前暴露还未确认的页面能力。
 */
const props = defineProps({
  collectionName: {
    type: String,
    default: ''
  },
  declareOriginal: {
    type: Boolean,
    default: false
  },
  originalType: {
    type: String,
    default: ''
  },
  contentDeclaration: {
    type: String,
    default: ''
  },
  isDraft: {
    type: Boolean,
    default: false
  }
})

const emit = defineEmits([
  'update:collectionName',
  'update:declareOriginal',
  'update:originalType',
  'update:contentDeclaration',
  'update:isDraft'
])

/**
 * 图文增强字段仍由父层维护，组件只负责把平台输入收口到统一事件。
 */
const collectionNameModel = computed({
  get: () => props.collectionName,
  set: (value) => emit('update:collectionName', value)
})

const declareOriginalModel = computed({
  get: () => props.declareOriginal,
  set: (value) => emit('update:declareOriginal', value)
})

const originalTypeModel = computed({
  get: () => props.originalType,
  set: (value) => emit('update:originalType', value)
})

const contentDeclarationModel = computed({
  get: () => props.contentDeclaration,
  set: (value) => emit('update:contentDeclaration', value)
})

const isDraftModel = computed({
  get: () => props.isDraft,
  set: (value) => emit('update:isDraft', value)
})
</script>
