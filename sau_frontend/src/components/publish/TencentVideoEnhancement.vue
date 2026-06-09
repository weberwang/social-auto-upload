<template>
  <div class="tencent-video-enhancement">
    <h3>视频号配置</h3>
    <el-input
      v-model="shortTitleModel"
      type="text"
      maxlength="16"
      placeholder="请输入短标题"
      class="tencent-short-title-input"
    />
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
    <el-input
      v-model="thumbnailLandscapePathModel"
      type="text"
      maxlength="500"
      placeholder="请输入 4:3 横版封面路径（可选）"
      class="tencent-thumbnail-landscape-input"
    />
    <el-input
      v-model="thumbnailPortraitPathModel"
      type="text"
      maxlength="500"
      placeholder="请输入 3:4 竖版封面路径（可选）"
      class="tencent-thumbnail-portrait-input"
    />
    <el-checkbox v-model="declareOriginalModel" label="声明原创" />
    <el-checkbox v-model="isDraftModel" label="仅保存草稿(用手机发布)" />
  </div>
</template>

<script setup>
import { computed } from 'vue'

/**
 * 视频号视频增强字段组件先接住页面输入，后续任务再把这些字段接到 payload 和 uploader。
 */
const props = defineProps({
  shortTitle: {
    type: String,
    default: ''
  },
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
  thumbnailLandscapePath: {
    type: String,
    default: ''
  },
  thumbnailPortraitPath: {
    type: String,
    default: ''
  },
  isDraft: {
    type: Boolean,
    default: false
  }
})

const emit = defineEmits([
  'update:shortTitle',
  'update:collectionName',
  'update:declareOriginal',
  'update:originalType',
  'update:contentDeclaration',
  'update:thumbnailLandscapePath',
  'update:thumbnailPortraitPath',
  'update:isDraft'
])

/**
 * 每个字段都通过单独事件回写，避免平台增强组件直接依赖父层实现细节。
 */
const shortTitleModel = computed({
  get: () => props.shortTitle,
  set: (value) => emit('update:shortTitle', value)
})

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

/**
 * 视频号视频支持双比例封面，这里分别暴露横版和竖版路径，避免继续挤进通用字段造成平台歧义。
 */
const thumbnailLandscapePathModel = computed({
  get: () => props.thumbnailLandscapePath,
  set: (value) => emit('update:thumbnailLandscapePath', value)
})

const thumbnailPortraitPathModel = computed({
  get: () => props.thumbnailPortraitPath,
  set: (value) => emit('update:thumbnailPortraitPath', value)
})

const isDraftModel = computed({
  get: () => props.isDraft,
  set: (value) => emit('update:isDraft', value)
})
</script>
