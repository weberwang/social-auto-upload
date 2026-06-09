import test from 'node:test'
import assert from 'node:assert/strict'

import { buildPublishPayloadFromState } from '../src/constants/publishPayload.js'
import { createDefaultPublishTabState, flattenPublishTabState } from '../src/constants/publishTabState.js'

test('抖音视频 payload 应包含平台增强字段', () => {
  const tab = flattenPublishTabState(createDefaultPublishTabState({
    platform: {
      selectedPlatform: 3,
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
      title: '抖音视频标题',
      topics: ['探店']
    },
    platformFields: {
      douyin: {
        productTitle: '示例商品',
        productLink: 'https://example.com/item',
        location: '上海市',
        selfDeclaration: '内容为个人观点或见解',
        syncToToutiaoXigua: false
      }
    }
  }))

  const payload = buildPublishPayloadFromState(tab, [
    { id: 'acct-1', filePath: 'douyin_creator.json', name: '抖音主号' }
  ])

  assert.deepEqual(payload.platformFields.douyin, {
    productTitle: '示例商品',
    productLink: 'https://example.com/item',
    location: '上海市',
    selfDeclaration: '内容为个人观点或见解',
    syncToToutiaoXigua: false
  })
  assert.deepEqual(payload.accountList, ['douyin_creator.json'])
})

test('抖音图文默认自主声明应可回填到扁平状态', () => {
  const tab = flattenPublishTabState(createDefaultPublishTabState({
    platform: {
      selectedPlatform: 3,
      contentType: 'image_text'
    }
  }))

  assert.equal(tab.selfDeclaration, '内容为个人观点或见解')
  assert.equal(tab.syncToToutiaoXigua, true)
})
