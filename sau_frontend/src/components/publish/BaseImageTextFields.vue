<template>
  <div class="base-image-text-fields">
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

    <div class="note-section">
      <h3>图文正文</h3>
      <el-input
        v-model="noteContentModel"
        type="textarea"
        :rows="6"
        :placeholder="notePlaceholder"
        maxlength="1000"
        show-word-limit
        class="title-input"
      />
    </div>
  </div>
</template>

<script setup>
import { computed } from 'vue'

/**
 * 图文基础字段组件统一封装标题和正文输入，避免各平台重复堆同一套表单。
 */
const props = defineProps({
  title: {
    type: String,
    default: ''
  },
  noteContent: {
    type: String,
    default: ''
  },
  notePlaceholder: {
    type: String,
    default: '请输入图文正文'
  }
})

const emit = defineEmits(['update:title', 'update:noteContent'])

/**
 * 基础图文字段仍由父层持有状态，这里只负责展示与回写。
 */
const titleModel = computed({
  get: () => props.title,
  set: (value) => emit('update:title', value)
})

const noteContentModel = computed({
  get: () => props.noteContent,
  set: (value) => emit('update:noteContent', value)
})
</script>
