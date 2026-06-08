import test from 'node:test'
import assert from 'node:assert/strict'

import { buildPublishPayloadFromState } from '../src/constants/publishPayload.js'
import { flattenPublishTabState, createDefaultPublishTabState } from '../src/constants/publishTabState.js'

test('视频号视频 payload 应包含基础字段与 tencent 平台增强字段', () => {
  const tab = flattenPublishTabState(createDefaultPublishTabState({
    platform: {
      selectedPlatform: 2,
      contentType: 'video'
    },
    materials: {
      fileList: [
        {
          name: 'video-a.mp4',
          path: '/media/video-a.mp4'
        }
      ]
    },
    accounts: {
      selectedAccountIds: ['acct-1']
    },
    baseFields: {
      title: '视频标题',
      description: '视频简介',
      topics: ['旅行'],
      scheduleEnabled: true,
      videosPerDay: 2,
      dailyTimes: ['10:00', '18:00'],
      startDays: 1
    },
    platformFields: {
      tencent: {
        collectionName: '旅行合集',
        declareOriginal: true,
        originalType: '生活',
        contentDeclaration: '无需声明',
        isDraft: true
      }
    }
  }))
  const payload = buildPublishPayloadFromState(tab, [
    { id: 'acct-1', filePath: 'tencent_creator.json', name: '视频号账号' }
  ])

  assert.equal(payload.type, 2)
  assert.equal(payload.contentType, 'video')
  assert.equal(payload.baseFields.title, '视频标题')
  assert.equal(payload.baseFields.description, '视频简介')
  assert.deepEqual(payload.baseFields.tags, ['旅行'])
  assert.equal(payload.platformFields.tencent.collectionName, '旅行合集')
  assert.equal(payload.platformFields.tencent.declareOriginal, true)
  assert.equal(payload.platformFields.tencent.isDraft, true)
  assert.deepEqual(payload.fileList, ['/media/video-a.mp4'])
  assert.deepEqual(payload.accountList, ['tencent_creator.json'])
})
