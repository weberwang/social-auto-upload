import test from 'node:test'
import assert from 'node:assert/strict'

import { buildPublishPayloadFromState } from '../src/constants/publishPayload.js'
import { createDefaultPublishTabState, flattenPublishTabState } from '../src/constants/publishTabState.js'

test('视频号视频 payload 应包含平台增强字段', () => {
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
      title: '视频号视频标题'
    },
    platformFields: {
      tencent: {
        shortTitle: '短标题',
        collectionName: '旅行合集',
        declareOriginal: true,
        originalType: '生活',
        contentDeclaration: '无需声明',
        thumbnailLandscapePath: 'landscape.png',
        thumbnailPortraitPath: 'portrait.png',
        isDraft: true
      }
    }
  }))

  const payload = buildPublishPayloadFromState(tab, [
    { id: 'acct-1', filePath: 'tencent_creator.json', name: '视频号主号' }
  ])

  assert.deepEqual(payload.platformFields.tencent, {
    shortTitle: '短标题',
    collectionName: '旅行合集',
    declareOriginal: true,
    originalType: '生活',
    contentDeclaration: '无需声明',
    noteCoverPath: '',
    thumbnailLandscapePath: 'landscape.png',
    thumbnailPortraitPath: 'portrait.png',
    isDraft: true
  })
  assert.deepEqual(payload.accountList, ['tencent_creator.json'])
})
