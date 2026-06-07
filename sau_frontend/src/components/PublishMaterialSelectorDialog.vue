<template>
  <el-dialog
    :model-value="visible"
    title="选择素材"
    width="960px"
    class="material-library-dialog"
    @update:model-value="emit('update:visible', $event)"
  >
    <div class="material-library-toolbar">
      <span class="material-library-toolbar__hint">
        {{ platformSupportsImageText
          ? `${platformName}支持图文发布，可选择视频或图片素材。`
          : `${platformName}仅支持视频发布，图片素材会显示但不可选。` }}
      </span>
      <el-button type="primary" @click="emit('upload')">上传素材</el-button>
    </div>

    <div v-if="rows.length === 0" class="material-library-empty">
      <el-empty :description="emptyState.description || '素材库暂无素材'">
        <el-button v-if="emptyState.showUploadAction" type="primary" @click="emit('upload')">上传素材</el-button>
      </el-empty>
    </div>

    <div v-else class="material-list">
      <el-table
        ref="tableRef"
        :data="rows"
        class="material-table"
        style="width: 100%"
        row-key="id"
        @selection-change="handleSelectionChange"
      >
        <el-table-column type="selection" width="55" :selectable="isRowSelectable" />
        <el-table-column label="UUID" width="220">
          <template #default="scope">
            <div class="material-cell material-cell--uuid">
              <span>{{ scope.row.uuid || scope.row.id }}</span>
            </div>
          </template>
        </el-table-column>
        <el-table-column label="文件名" min-width="320">
          <template #default="scope">
            <div class="material-cell material-cell--filename">
              <strong>{{ scope.row.filename }}</strong>
              <span>{{ scope.row.file_path }}</span>
            </div>
          </template>
        </el-table-column>
        <el-table-column label="备注" min-width="220" show-overflow-tooltip>
          <template #default="scope">
            <span
              class="material-remark"
              :class="{ 'material-remark--empty': !scope.row.remark }"
            >
              {{ scope.row.remark || '暂无备注' }}
            </span>
          </template>
        </el-table-column>
        <el-table-column label="类型" width="110">
          <template #default="scope">
            <el-tag :type="getMaterialTypeTag(scope.row.filename)" effect="plain" size="small">
              {{ getMaterialType(scope.row.filename) }}
            </el-tag>
          </template>
        </el-table-column>
        <el-table-column label="可选状态" width="110">
          <template #default="scope">
            <el-tag :type="scope.row.compatible ? 'success' : 'info'" effect="plain" size="small">
              {{ scope.row.compatible ? '可选' : '不兼容' }}
            </el-tag>
          </template>
        </el-table-column>
        <el-table-column label="提示" min-width="220" show-overflow-tooltip>
          <template #default="scope">
            <span class="material-compatibility-message">
              {{ scope.row.compatibilityMessage }}
            </span>
          </template>
        </el-table-column>
        <el-table-column prop="filesize" label="文件大小" width="120">
          <template #default="scope">
            {{ scope.row.filesize }} MB
          </template>
        </el-table-column>
        <el-table-column prop="upload_time" label="上传时间" min-width="180" />
        <el-table-column label="操作" width="110" align="right">
          <template #default="scope">
            <div class="material-actions">
              <el-button size="small" @click="emit('preview', scope.row)">预览</el-button>
            </div>
          </template>
        </el-table-column>
      </el-table>
    </div>

    <template #footer>
      <div class="dialog-footer">
        <el-button @click="emit('update:visible', false)">取消</el-button>
        <el-button type="primary" @click="emit('confirm')">确定</el-button>
      </div>
    </template>
  </el-dialog>
</template>

<script setup>
import { nextTick, ref, watch } from 'vue'
import { getMaterialType, getMaterialTypeTag } from '@/constants/materialFormats'
import { areSelectedMaterialIdsEqual } from '@/constants/publishMaterials'

const props = defineProps({
  visible: {
    type: Boolean,
    required: true
  },
  rows: {
    type: Array,
    required: true
  },
  platformName: {
    type: String,
    required: true
  },
  platformSupportsImageText: {
    type: Boolean,
    required: true
  },
  selectedMaterialIds: {
    type: Array,
    required: true
  },
  emptyState: {
    type: Object,
    required: true
  }
})

const emit = defineEmits([
  'update:visible',
  'update:selectedMaterialIds',
  'preview',
  'upload',
  'confirm'
])

const tableRef = ref(null)
const isSyncingSelection = ref(false)

/**
 * 不兼容素材仍然展示，但禁止勾选，这样用户能看到全量素材而不会误发错内容类型。
 */
const isRowSelectable = (row) => row.compatible

/**
 * 把表格勾选状态同步回父组件，统一由父层维护最终选中的素材 ID 列表。
 */
const handleSelectionChange = (selection) => {
  if (isSyncingSelection.value) {
    return
  }

  const nextSelectedIds = selection.map((item) => item.id)
  if (areSelectedMaterialIdsEqual(props.selectedMaterialIds, nextSelectedIds)) {
    return
  }

  emit('update:selectedMaterialIds', nextSelectedIds)
}

/**
 * 每次弹窗打开或数据变化后，都需要把外部选中态重新同步到表格实例。
 */
const syncTableSelection = async () => {
  await nextTick()
  if (!tableRef.value) {
    return
  }

  isSyncingSelection.value = true
  try {
    tableRef.value.clearSelection()
    const selectedIdSet = new Set(props.selectedMaterialIds)
    props.rows
      .filter((row) => row.compatible && selectedIdSet.has(row.id))
      .forEach((row) => {
        tableRef.value.toggleRowSelection(row, true)
      })
  } finally {
    isSyncingSelection.value = false
  }
}

watch(
  () => [props.visible, props.rows, props.selectedMaterialIds],
  () => {
    if (props.visible) {
      syncTableSelection()
    }
  },
  { deep: true }
)
</script>

<style scoped lang="scss">
.material-library-toolbar {
  display: flex;
  justify-content: space-between;
  align-items: center;
  gap: 16px;
  margin-bottom: 16px;

  &__hint {
    color: #606266;
    font-size: 14px;
    line-height: 1.5;
  }
}

.material-cell {
  display: flex;
  flex-direction: column;
  gap: 4px;

  &--uuid {
    word-break: break-all;
  }

  &--filename {
    strong {
      color: #303133;
      font-weight: 600;
    }

    span {
      color: #909399;
      font-size: 12px;
      word-break: break-all;
    }
  }
}

.material-remark {
  color: #606266;

  &--empty {
    color: #c0c4cc;
  }
}

.material-actions {
  display: flex;
  justify-content: flex-end;
}

.material-compatibility-message {
  color: #606266;
  font-size: 13px;
}

.dialog-footer {
  text-align: right;
}
</style>
