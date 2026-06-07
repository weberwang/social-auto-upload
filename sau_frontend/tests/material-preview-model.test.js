import test from 'node:test'
import assert from 'node:assert/strict'

import {
  createPreviewItemFromMaterial,
  createPreviewItemFromPublishFile
} from '../src/composables/materialPreviewModel.js'

test('素材记录应转换为共享预览对象', () => {
  const result = createPreviewItemFromMaterial({
    filename: 'demo.mp4',
    file_path: 'uuid_demo.mp4',
    filesize: 12.34,
    upload_time: '2026-06-06 20:00:00',
    remark: '首页主视觉'
  })

  assert.deepEqual(result, {
    filename: 'demo.mp4',
    file_path: 'uuid_demo.mp4',
    filesize: 12.34,
    upload_time: '2026-06-06 20:00:00',
    remark: '首页主视觉'
  })
})

test('发布中心文件应转换为共享预览对象并换算大小', () => {
  const result = createPreviewItemFromPublishFile({
    name: 'demo.mp4',
    path: 'uuid_demo.mp4',
    size: 3 * 1024 * 1024 + 512 * 1024
  })

  assert.deepEqual(result, {
    filename: 'demo.mp4',
    file_path: 'uuid_demo.mp4',
    filesize: 3.5,
    upload_time: '',
    remark: ''
  })
})
