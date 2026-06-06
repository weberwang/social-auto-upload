<template>
  <div class="bilibili-section">
    <h3>B站配置</h3>
    <el-input
      v-model="descriptionModel"
      type="textarea"
      :rows="4"
      placeholder="请输入B站简介"
      maxlength="2000"
      show-word-limit
      class="bilibili-description-input"
    />
    <el-select
      v-model="tidModel"
      clearable
      filterable
      placeholder="请选择B站分区"
      class="bilibili-tid-select"
    >
      <el-option-group
        v-for="group in BILIBILI_CATEGORY_GROUPS"
        :key="group.label"
        :label="group.label"
      >
        <el-option
          v-for="option in group.options"
          :key="`${group.label}-${option.value}`"
          :label="option.label"
          :value="option.value"
        />
      </el-option-group>
    </el-select>
  </div>
</template>

<script setup>
import { computed } from 'vue'
import { BILIBILI_CATEGORY_GROUPS } from '@/constants/bilibiliCategories'

/**
 * B站专属表单字段单独拆组件，避免发布中心主视图继续膨胀。
 */
const props = defineProps({
  description: {
    type: String,
    default: ''
  },
  bilibiliTid: {
    type: Number,
    default: null
  }
})

const emit = defineEmits(['update:description', 'update:bilibiliTid'])

const descriptionModel = computed({
  get: () => props.description,
  set: (value) => emit('update:description', value)
})

/**
 * 直接把分区 tid 存进表单状态，避免中文展示值和接口值在提交前再次转换。
 */
const tidModel = computed({
  get: () => props.bilibiliTid,
  set: (value) => emit('update:bilibiliTid', value)
})
</script>

<style scoped>
.bilibili-tid-select {
  width: 100%;
}
</style>
