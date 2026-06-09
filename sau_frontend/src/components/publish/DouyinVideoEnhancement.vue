<template>
  <div class="douyin-video-enhancement">
    <h3>抖音配置</h3>
    <el-input
      v-model="productTitleModel"
      type="text"
      maxlength="20"
      placeholder="请输入商品标题（可选）"
      class="douyin-product-title-input"
    />
    <el-input
      v-model="productLinkModel"
      type="text"
      maxlength="500"
      placeholder="请输入商品链接（可选）"
      class="douyin-product-link-input"
    />
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
    <el-checkbox v-model="syncToToutiaoXiguaModel" label="同步发布到西瓜视频/今日头条（若账号支持）" />
  </div>
</template>

<script setup>
import { computed } from 'vue'

/**
 * 抖音视频增强字段组件收口商品、位置和分发开关，避免发布中心继续把平台专属逻辑散落在主页面。
 */
const props = defineProps({
  productTitle: {
    type: String,
    default: ''
  },
  productLink: {
    type: String,
    default: ''
  },
  location: {
    type: String,
    default: ''
  },
  selfDeclaration: {
    type: String,
    default: ''
  },
  syncToToutiaoXigua: {
    type: Boolean,
    default: true
  }
})

const emit = defineEmits([
  'update:productTitle',
  'update:productLink',
  'update:location',
  'update:selfDeclaration',
  'update:syncToToutiaoXigua'
])

/**
 * 自主声明先保留为自由文本，避免把页面上可能变化的枚举值硬编码到前端常量里。
 */
const productTitleModel = computed({
  get: () => props.productTitle,
  set: (value) => emit('update:productTitle', value)
})

const productLinkModel = computed({
  get: () => props.productLink,
  set: (value) => emit('update:productLink', value)
})

const locationModel = computed({
  get: () => props.location,
  set: (value) => emit('update:location', value)
})

const selfDeclarationModel = computed({
  get: () => props.selfDeclaration,
  set: (value) => emit('update:selfDeclaration', value)
})

const syncToToutiaoXiguaModel = computed({
  get: () => props.syncToToutiaoXigua,
  set: (value) => emit('update:syncToToutiaoXigua', value)
})
</script>
