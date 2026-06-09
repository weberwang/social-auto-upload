<template>
  <DouyinVideoEnhancement
    v-if="componentName === 'DouyinVideoEnhancement'"
    v-model:product-title="tab.productTitle"
    v-model:product-link="tab.productLink"
    v-model:location="tab.location"
    v-model:self-declaration="tab.selfDeclaration"
    v-model:sync-to-toutiao-xigua="tab.syncToToutiaoXigua"
  />

  <DouyinImageTextEnhancement
    v-else-if="componentName === 'DouyinImageTextEnhancement'"
    v-model:location="tab.location"
    v-model:self-declaration="tab.selfDeclaration"
  />

  <KuaishouVideoEnhancement
    v-else-if="componentName === 'KuaishouVideoEnhancement'"
    v-model:thumbnail-path="tab.thumbnailPath"
  />

  <XiaohongshuVideoEnhancement
    v-else-if="componentName === 'XiaohongshuVideoEnhancement'"
    v-model:thumbnail-path="tab.xiaohongshuThumbnailPath"
    v-model:location="tab.location"
  />

  <XiaohongshuImageTextEnhancement
    v-else-if="componentName === 'XiaohongshuImageTextEnhancement'"
    v-model:location="tab.location"
  />

  <TencentVideoEnhancement
    v-else-if="componentName === 'TencentVideoEnhancement'"
    v-model:short-title="tab.shortTitle"
    v-model:collection-name="tab.collectionName"
    v-model:declare-original="tab.declareOriginal"
    v-model:original-type="tab.originalType"
    v-model:content-declaration="tab.contentDeclaration"
    v-model:thumbnail-landscape-path="tab.thumbnailLandscapePath"
    v-model:thumbnail-portrait-path="tab.thumbnailPortraitPath"
    v-model:is-draft="tab.isDraft"
  />

  <TencentImageTextEnhancement
    v-else-if="componentName === 'TencentImageTextEnhancement'"
    v-model:collection-name="tab.collectionName"
    v-model:declare-original="tab.declareOriginal"
    v-model:original-type="tab.originalType"
    v-model:content-declaration="tab.contentDeclaration"
    v-model:is-draft="tab.isDraft"
  />

  <BilibiliPublishFields
    v-else-if="componentName === 'BilibiliPublishFields'"
    v-model:description="tab.description"
    v-model:bilibili-tid="tab.bilibiliTid"
  />
</template>

<script setup>
import { computed } from 'vue'

import BilibiliPublishFields from '@/components/BilibiliPublishFields.vue'
import DouyinImageTextEnhancement from '@/components/publish/DouyinImageTextEnhancement.vue'
import DouyinVideoEnhancement from '@/components/publish/DouyinVideoEnhancement.vue'
import KuaishouVideoEnhancement from '@/components/publish/KuaishouVideoEnhancement.vue'
import TencentImageTextEnhancement from '@/components/publish/TencentImageTextEnhancement.vue'
import TencentVideoEnhancement from '@/components/publish/TencentVideoEnhancement.vue'
import XiaohongshuImageTextEnhancement from '@/components/publish/XiaohongshuImageTextEnhancement.vue'
import XiaohongshuVideoEnhancement from '@/components/publish/XiaohongshuVideoEnhancement.vue'
import { getPlatformEnhancementComponentName } from '@/constants/publishTabState.js'

/**
 * 平台增强装配器只负责根据平台和内容类型决定挂哪个增强组件，不承载业务校验。
 */
const props = defineProps({
  tab: {
    type: Object,
    required: true
  }
})

/**
 * 增强组件名称通过纯函数决策，后续补平台时只扩映射，不再膨胀主视图模板。
 */
const componentName = computed(() => (
  getPlatformEnhancementComponentName(props.tab.selectedPlatform, props.tab.contentType)
))
</script>
