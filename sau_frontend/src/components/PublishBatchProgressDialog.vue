<template>
  <el-dialog
    :model-value="visible"
    title="批量发布进度"
    width="500px"
    :close-on-click-modal="false"
    :close-on-press-escape="false"
    :show-close="false"
    @update:model-value="$emit('update:visible', $event)"
  >
    <div class="publish-progress">
      <el-progress
        :percentage="progress"
        :status="progress === 100 ? 'success' : ''"
      />
      <div v-if="currentTab" class="current-publishing">
        正在发布：{{ currentTab.label }}
      </div>

      <div class="publish-results" v-if="results.length > 0">
        <div
          v-for="(result, index) in results"
          :key="index"
          :class="['result-item', result.status]"
        >
          <el-icon v-if="result.status === 'success'"><Check /></el-icon>
          <el-icon v-else-if="result.status === 'error'"><Close /></el-icon>
          <el-icon v-else><InfoFilled /></el-icon>
          <span class="label">{{ result.label }}</span>
          <span class="message">{{ result.message }}</span>
        </div>
      </div>
    </div>

    <template #footer>
      <div class="dialog-footer">
        <el-button
          @click="$emit('cancel')"
          :disabled="progress === 100"
        >
          取消发布
        </el-button>
        <el-button
          type="primary"
          @click="$emit('update:visible', false)"
          v-if="progress === 100"
        >
          关闭
        </el-button>
      </div>
    </template>
  </el-dialog>
</template>

<script setup>
import { Check, Close, InfoFilled } from '@element-plus/icons-vue'

/**
 * 批量发布进度弹窗。
 * 独立承载进度展示与结果列表，减少发布中心主视图模板体积。
 */
defineProps({
  visible: {
    type: Boolean,
    default: false
  },
  progress: {
    type: Number,
    default: 0
  },
  currentTab: {
    type: Object,
    default: null
  },
  results: {
    type: Array,
    default: () => []
  }
})

defineEmits(['cancel', 'update:visible'])
</script>

<style scoped lang="scss">
.publish-progress {
  padding: 20px;

  .current-publishing {
    margin: 15px 0;
    text-align: center;
    color: #606266;
  }

  .publish-results {
    margin-top: 20px;
    border-top: 1px solid #ebeef5;
    padding-top: 15px;
    max-height: 300px;
    overflow-y: auto;

    .result-item {
      display: flex;
      align-items: center;
      padding: 8px 0;
      color: #606266;

      .el-icon {
        margin-right: 8px;
      }

      .label {
        margin-right: 10px;
        font-weight: 500;
      }

      .message {
        color: #909399;
      }

      &.success {
        color: #67c23a;
      }

      &.error {
        color: #f56c6c;
      }

      &.cancelled {
        color: #909399;
      }
    }
  }
}

.dialog-footer {
  text-align: right;
}
</style>
