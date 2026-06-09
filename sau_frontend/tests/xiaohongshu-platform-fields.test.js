import test from 'node:test'
import assert from 'node:assert/strict'

import { buildPublishPayloadFromState } from '../src/constants/publishPayload.js'
import { createDefaultPublishTabState, flattenPublishTabState } from '../src/constants/publishTabState.js'

test('小红书视频 payload 应包含平台增强字段', () => {
  const tab = flattenPublishTabState(createDefaultPublishTabState({
    platform: {
      selectedPlatform: 1,
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
      title: '小红书视频标题'
    },
    platformFields: {
      xiaohongshu: {
        thumbnailPath: 'cover.png',
        location: '上海市'
      }
    }
  }))

  const payload = buildPublishPayloadFromState(tab, [
    { id: 'acct-1', filePath: 'xiaohongshu_creator.json', name: '小红书主号' }
  ])

  assert.deepEqual(payload.platformFields.xiaohongshu, {
    thumbnailPath: 'cover.png',
    location: '上海市'
  })
  assert.deepEqual(payload.accountList, ['xiaohongshu_creator.json'])
})
