import test from 'node:test'
import assert from 'node:assert/strict'

import {
  buildMaterialUploadFormData,
  syncMaterialRemarks
} from '../src/composables/materialUploadForm.js'

test('素材上传表单应为每个文件单独保留备注', () => {
  const result = syncMaterialRemarks(
    [
      { uid: 'file-1', name: 'a.mp4' },
      { uid: 'file-2', name: 'b.jpg' }
    ],
    {
      'file-1': '视频备注',
      stale: '应被清理'
    }
  )

  assert.deepEqual(result, {
    'file-1': '视频备注',
    'file-2': ''
  })
})

test('素材上传表单应提交备注而不是自定义文件名', () => {
  const formData = buildMaterialUploadFormData({
    file: { raw: new Blob(['demo']), name: 'sample.mp4' },
    remark: '首页主视觉素材'
  })

  assert.equal(formData.get('remark'), '首页主视觉素材')
  assert.equal(formData.get('filename'), null)
  assert.ok(formData.get('file') instanceof Blob)
})
