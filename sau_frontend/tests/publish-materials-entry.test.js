import test from 'node:test'
import assert from 'node:assert/strict'

import {
  areSelectedMaterialIdsEqual,
  buildPublishMaterialSelectionRows,
  getMaterialLibraryEmptyState,
  getEmptyFileMessage,
  getUploadButtonText
} from '../src/constants/publishMaterials.js'
import {
  PUBLISH_CONTENT_TYPE_IMAGE_TEXT,
  PUBLISH_CONTENT_TYPE_VIDEO
} from '../src/constants/publishPlatforms.js'

test('发布中心素材入口按钮应统一显示为选择素材', () => {
  assert.equal(getUploadButtonText(PUBLISH_CONTENT_TYPE_VIDEO), '选择素材')
  assert.equal(getUploadButtonText(PUBLISH_CONTENT_TYPE_IMAGE_TEXT), '选择素材')
})

test('发布中心缺少素材时应提示先选择素材', () => {
  assert.equal(getEmptyFileMessage(PUBLISH_CONTENT_TYPE_VIDEO), '请先选择素材')
  assert.equal(getEmptyFileMessage(PUBLISH_CONTENT_TYPE_IMAGE_TEXT), '请先选择素材')
})

test('支持图文的平台应允许选择图片素材', () => {
  assert.deepEqual(
    buildPublishMaterialSelectionRows(
      [
        { id: 1, filename: 'cover-a.jpg', remark: '', filesize: 1.2, upload_time: '2026-06-08 10:00:00', file_path: 'a.jpg' },
        { id: 2, filename: 'clip-a.mp4', remark: '主片', filesize: 24.5, upload_time: '2026-06-08 11:00:00', file_path: 'a.mp4' }
      ],
      1
    ).map(({ id, filename, compatible, selectionContentType }) => ({ id, filename, compatible, selectionContentType })),
    [
      { id: 1, filename: 'cover-a.jpg', compatible: true, selectionContentType: PUBLISH_CONTENT_TYPE_IMAGE_TEXT },
      { id: 2, filename: 'clip-a.mp4', compatible: true, selectionContentType: PUBLISH_CONTENT_TYPE_VIDEO }
    ]
  )
})

test('不支持图文的平台应提示图片不可选', () => {
  assert.deepEqual(
    buildPublishMaterialSelectionRows(
      [
        { id: 1, filename: 'cover-a.jpg', remark: '', filesize: 1.2, upload_time: '2026-06-08 10:00:00', file_path: 'a.jpg' }
      ],
      2
    ).map(({ id, filename, compatible, compatibilityMessage }) => ({ id, filename, compatible, compatibilityMessage })),
    [
      {
        id: 1,
        filename: 'cover-a.jpg',
        compatible: false,
        compatibilityMessage: '视频号当前不支持图文发布，图片素材不可选。'
      }
    ]
  )
})

test('素材库为空时应提示先上传素材', () => {
  assert.deepEqual(
    getMaterialLibraryEmptyState(
      [],
      1
    ),
    {
      description: '素材库暂无素材，请先上传素材。',
      showUploadAction: true
    }
  )
})

test('相同素材选择集即使顺序不同也应视为同一次选择', () => {
  assert.equal(areSelectedMaterialIdsEqual([1, 2], [2, 1]), true)
  assert.equal(areSelectedMaterialIdsEqual([1, 2], [1, 2, 3]), false)
})
