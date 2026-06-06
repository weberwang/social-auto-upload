import { ref } from 'vue'

import {
  createPreviewItemFromMaterial,
  createPreviewItemFromPublishFile
} from '@/composables/materialPreviewModel.js'

/**
 * 统一管理素材预览弹窗状态，避免多个页面各自维护一套预览对象转换逻辑。
 */
export function useMaterialPreviewDialog() {
  const previewDialogVisible = ref(false)
  const currentPreviewMaterial = ref(null)

  const openMaterialPreview = (material) => {
    currentPreviewMaterial.value = createPreviewItemFromMaterial(material)
    previewDialogVisible.value = true
  }

  const openPublishFilePreview = (file) => {
    currentPreviewMaterial.value = createPreviewItemFromPublishFile(file)
    previewDialogVisible.value = true
  }

  return {
    previewDialogVisible,
    currentPreviewMaterial,
    openMaterialPreview,
    openPublishFilePreview
  }
}
