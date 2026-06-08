<template>
  <div class="tab-management">
    <div class="tab-header">
      <div class="tab-list">
        <div
          v-for="tab in tabs"
          :key="tab.name"
          :class="['tab-item', { active: activeTab === tab.name }]"
          @click="$emit('select-tab', tab.name)"
        >
          <span>{{ tab.label }}</span>
          <el-icon
            v-if="tabs.length > 1"
            class="close-icon"
            @click.stop="$emit('remove-tab', tab.name)"
          >
            <Close />
          </el-icon>
        </div>
      </div>
      <div class="tab-actions">
        <PublishDraftActions
          :visible="draftDialogVisible"
          :loading="draftLoading"
          :drafts="draftItems"
          :current-draft-name="currentDraftName"
          @save="$emit('save-draft')"
          @open="$emit('open-draft')"
          @refresh="$emit('refresh-drafts')"
          @load="$emit('load-draft', $event)"
          @delete="$emit('remove-draft', $event)"
          @update:visible="$emit('update:draft-visible', $event)"
        />
        <el-dropdown trigger="click" @command="$emit('copy-tab', $event)">
          <el-button
            type="primary"
            size="small"
            class="add-tab-btn"
          >
            <el-icon><DocumentCopy /></el-icon>
            复制内容
            <el-icon class="el-icon--right"><ArrowDown /></el-icon>
          </el-button>
            <template #dropdown>
              <el-dropdown-menu>
                <el-dropdown-item command="copy_all">
                  复制全部平台
                </el-dropdown-item>
                <el-dropdown-item divided disabled>
                  选择单个平台
                </el-dropdown-item>
                <el-dropdown-item
                  v-for="platform in platforms"
                  :key="platform.key"
                :command="platform.key"
              >
                复制到{{ platform.name }}
              </el-dropdown-item>
            </el-dropdown-menu>
          </template>
        </el-dropdown>
        <el-button
          type="success"
          size="small"
          :loading="batchPublishing"
          class="batch-publish-btn"
          @click="$emit('batch-publish')"
        >
          批量发布
        </el-button>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ArrowDown, Close, DocumentCopy } from '@element-plus/icons-vue'
import PublishDraftActions from '@/components/PublishDraftActions.vue'

/**
 * 发布中心顶部的 Tab 与草稿操作条单独拆分，避免主页面继续堆叠交互模板。
 */
defineProps({
  tabs: {
    type: Array,
    required: true
  },
  activeTab: {
    type: String,
    required: true
  },
  platforms: {
    type: Array,
    required: true
  },
  batchPublishing: {
    type: Boolean,
    required: true
  },
  draftDialogVisible: {
    type: Boolean,
    required: true
  },
  draftLoading: {
    type: Boolean,
    required: true
  },
  draftItems: {
    type: Array,
    required: true
  },
  currentDraftName: {
    type: String,
    default: ''
  }
})

defineEmits([
  'batch-publish',
  'copy-tab',
  'load-draft',
  'open-draft',
  'refresh-drafts',
  'remove-draft',
  'remove-tab',
  'save-draft',
  'select-tab',
  'update:draft-visible'
])
</script>

<style lang="scss" scoped>
.tab-management {
  background-color: #fff;
  border-radius: 4px;
  box-shadow: 0 2px 12px 0 rgba(0, 0, 0, 0.1);
  margin-bottom: 20px;
  padding: 15px 20px;

  .tab-header {
    display: flex;
    align-items: flex-start;
    gap: 15px;

    .tab-list {
      display: flex;
      flex: 1;
      flex-wrap: wrap;
      gap: 10px;
      min-width: 0;

      .tab-item {
        display: flex;
        align-items: center;
        gap: 6px;
        height: 32px;
        padding: 6px 12px;
        font-size: 14px;
        background-color: #f5f7fa;
        border: 1px solid #dcdfe6;
        border-radius: 4px;
        cursor: pointer;
        transition: all 0.3s;

        &:hover {
          background-color: #ecf5ff;
          border-color: #b3d8ff;
        }

        &.active {
          color: #fff;
          background-color: #409eff;
          border-color: #409eff;

          .close-icon {
            color: #fff;

            &:hover {
              background-color: rgba(255, 255, 255, 0.2);
            }
          }
        }

        .close-icon {
          padding: 2px;
          font-size: 12px;
          cursor: pointer;
          border-radius: 2px;
          transition: background-color 0.3s;

          &:hover {
            background-color: rgba(0, 0, 0, 0.1);
          }
        }
      }
    }

    .tab-actions {
      display: flex;
      flex-shrink: 0;
      gap: 10px;

      .add-tab-btn,
      .batch-publish-btn {
        display: flex;
        align-items: center;
        gap: 4px;
        height: 32px;
        padding: 6px 12px;
        font-size: 14px;
        white-space: nowrap;
      }
    }
  }
}
</style>
