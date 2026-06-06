import test from 'node:test'
import assert from 'node:assert/strict'

import { summarizeMaterialUploadResults } from '../src/composables/materialUploadBatch.js'

test('批量上传全部成功后应自动关闭上传弹窗', () => {
  const result = summarizeMaterialUploadResults([
    { status: 'success' },
    { status: 'success' }
  ])

  assert.deepEqual(result, {
    totalCount: 2,
    successCount: 2,
    failureCount: 0,
    shouldCloseDialog: true
  })
})

test('批量上传存在失败时不应自动关闭上传弹窗', () => {
  const result = summarizeMaterialUploadResults([
    { status: 'success' },
    { status: 'failure' }
  ])

  assert.deepEqual(result, {
    totalCount: 2,
    successCount: 1,
    failureCount: 1,
    shouldCloseDialog: false
  })
})
