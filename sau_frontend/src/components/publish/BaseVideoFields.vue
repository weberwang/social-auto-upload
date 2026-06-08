<template>
  <div class="base-video-fields">
    <div class="title-section">
      <h3>标题</h3>
      <el-input
        v-model="titleModel"
        type="textarea"
        :rows="3"
        placeholder="请输入标题"
        maxlength="100"
        show-word-limit
        class="title-input"
      />
    </div>
  </div>
</template>

<script setup>
import { computed } from 'vue'

/**
 * 视频基础字段组件先承载所有平台共用的标题输入，后续再逐步扩到描述、话题和定时。
 */
const props = defineProps({
  title: {
    type: String,
    default: ''
  }
})

const emit = defineEmits(['update:title'])

/**
 * 标题统一通过组件事件回写，避免主页面继续维护重复输入结构。
 */
const titleModel = computed({
  get: () => props.title,
  set: (value) => emit('update:title', value)
})
</script>
