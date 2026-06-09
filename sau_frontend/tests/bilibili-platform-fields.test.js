import test from 'node:test'
import assert from 'node:assert/strict'

import { buildPublishPayloadFromState } from '../src/constants/publishPayload.js'
import { createDefaultPublishTabState, flattenPublishTabState } from '../src/constants/publishTabState.js'

test('B站视频 payload 应把简介和分区放进 bilibili 平台字段', () => {
  const tab = flattenPublishTabState(createDefaultPublishTabState({
    platform: {
      selectedPlatform: 5,
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
      title: 'B站视频标题',
      description: ''
    },
    platformFields: {
      bilibili: {
        description: 'B站视频简介',
        tid: 17
      }
    }
  }))

  const payload = buildPublishPayloadFromState(tab, [
    { id: 'acct-1', filePath: 'bilibili_creator.json', name: 'B站主号' }
  ])

  assert.equal(payload.baseFields.description, '')
  assert.deepEqual(payload.platformFields.bilibili, {
    description: 'B站视频简介',
    tid: 17
  })
  assert.deepEqual(payload.accountList, ['bilibili_creator.json'])
})
