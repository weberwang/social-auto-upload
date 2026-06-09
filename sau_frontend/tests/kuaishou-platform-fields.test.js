import test from 'node:test'
import assert from 'node:assert/strict'

import { buildPublishPayloadFromState } from '../src/constants/publishPayload.js'
import { createDefaultPublishTabState, flattenPublishTabState } from '../src/constants/publishTabState.js'

test('快手视频 payload 应包含自定义封面字段', () => {
  const tab = flattenPublishTabState(createDefaultPublishTabState({
    platform: {
      selectedPlatform: 4,
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
      title: '快手视频标题'
    },
    platformFields: {
      kuaishou: {
        thumbnailPath: 'cover.png'
      }
    }
  }))

  const payload = buildPublishPayloadFromState(tab, [
    { id: 'acct-1', filePath: 'kuaishou_creator.json', name: '快手主号' }
  ])

  assert.deepEqual(payload.platformFields.kuaishou, {
    thumbnailPath: 'cover.png'
  })
  assert.deepEqual(payload.accountList, ['kuaishou_creator.json'])
})
