<template>
  <div class="publish-draft-actions">
    <el-button size="small" @click="$emit('save')" class="draft-action-btn">
      保存草稿
    </el-button>
    <el-button size="small" plain @click="$emit('open')" class="draft-action-btn">
      加载草稿
    </el-button>

    <el-dialog
      :model-value="visible"
      title="加载草稿"
      width="640px"
      class="draft-dialog"
      @update:model-value="$emit('update:visible', $event)"
    >
      <div class="draft-dialog-content">
        <div class="draft-dialog-toolbar">
          <div class="draft-summary">
            <span class="label">当前草稿：</span>
            <span class="value">{{ currentDraftName || '未绑定' }}</span>
          </div>
          <el-button size="small" @click="$emit('refresh')" :loading="loading">
            刷新列表
          </el-button>
        </div>

        <el-empty v-if="!loading && drafts.length === 0" description="暂无草稿，请先保存一份工作区草稿" />

        <div v-else class="draft-list">
          <div v-for="draft in drafts" :key="draft.id" class="draft-item">
            <div class="draft-meta">
              <div class="draft-name">{{ draft.name }}</div>
              <div class="draft-time">
                更新时间：{{ draft.updated_at }}
              </div>
            </div>
            <div class="draft-operations">
              <el-button size="small" type="primary" @click="$emit('load', draft)">
                加载
              </el-button>
              <el-button size="small" type="danger" plain @click="$emit('delete', draft)">
                删除
              </el-button>
            </div>
          </div>
        </div>
      </div>
    </el-dialog>
  </div>
</template>

<script setup>
/**
 * 发布中心草稿操作条。
 * 单独抽出草稿按钮与列表弹窗，避免主视图继续膨胀。
 */
defineProps({
  visible: {
    type: Boolean,
    default: false
  },
  loading: {
    type: Boolean,
    default: false
  },
  drafts: {
    type: Array,
    default: () => []
  },
  currentDraftName: {
    type: String,
    default: ''
  }
})

defineEmits(['save', 'open', 'refresh', 'load', 'delete', 'update:visible'])
</script>

<style scoped lang="scss">
.publish-draft-actions {
  display: flex;
  gap: 10px;

  .draft-action-btn {
    height: 32px;
    padding: 6px 12px;
    font-size: 14px;
    white-space: nowrap;
  }
}

.draft-dialog {
  .draft-dialog-content {
    display: flex;
    flex-direction: column;
    gap: 16px;
  }

  .draft-dialog-toolbar {
    display: flex;
    align-items: center;
    justify-content: space-between;
    gap: 12px;
  }

  .draft-summary {
    color: #606266;
    font-size: 14px;

    .label {
      margin-right: 6px;
    }

    .value {
      color: #303133;
      font-weight: 500;
    }
  }

  .draft-list {
    display: flex;
    flex-direction: column;
    gap: 12px;
    max-height: 360px;
    overflow-y: auto;
  }

  .draft-item {
    display: flex;
    align-items: center;
    justify-content: space-between;
    gap: 16px;
    padding: 14px 16px;
    border: 1px solid #ebeef5;
    border-radius: 8px;
    background: #fafafa;
  }

  .draft-meta {
    min-width: 0;
  }

  .draft-name {
    color: #303133;
    font-size: 15px;
    font-weight: 600;
    margin-bottom: 6px;
    word-break: break-all;
  }

  .draft-time {
    color: #909399;
    font-size: 13px;
  }

  .draft-operations {
    display: flex;
    gap: 8px;
    flex-shrink: 0;
  }
}
</style>
