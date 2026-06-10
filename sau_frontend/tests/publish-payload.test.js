import test from 'node:test'
import assert from 'node:assert/strict'

import { buildPublishPayloadFromState } from '../src/constants/publishPayload.js'
import { createDefaultPublishTabState, flattenPublishTabState } from '../src/constants/publishTabState.js'

test('视频号视频 payload 应包含基础字段和 tencent 平台增强字段', () => {
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

test('多账号发布时 payload 应映射全部账号文件与账号名称', () => {
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
      selectedAccountIds: ['acct-1', 'acct-2']
    },
    baseFields: {
      title: '批量账号标题'
    }
  }))
  const payload = buildPublishPayloadFromState(tab, [
    { id: 'acct-1', filePath: 'douyin_creator_1.json', name: '抖音主号' },
    { id: 'acct-2', filePath: 'douyin_creator_2.json', name: '抖音备用号' }
  ])

  assert.deepEqual(payload.accountList, ['douyin_creator_1.json', 'douyin_creator_2.json'])
  assert.deepEqual(payload.accountNameList, ['抖音主号', '抖音备用号'])
})

test('微信公众号图文 payload 应保留图文内容并映射公众号账号文件', () => {
  const tab = flattenPublishTabState(createDefaultPublishTabState({
    platform: {
      selectedPlatform: 6,
      contentType: 'image_text'
    },
    materials: {
      fileList: [
        {
          name: 'cover.png',
          path: '/media/cover.png'
        },
        {
          name: 'detail-1.png',
          path: '/media/detail-1.png'
        }
      ]
    },
    accounts: {
      selectedAccountIds: ['acct-1']
    },
    baseFields: {
      title: '公众号图文标题',
      noteContent: '公众号图文正文',
      topics: ['公众号', '测试']
    }
  }))
  const payload = buildPublishPayloadFromState(tab, [
    { id: 'acct-1', filePath: 'wechatmp_creator.json', name: '微信公众号账号' }
  ])

  assert.equal(payload.type, 6)
  assert.equal(payload.contentType, 'image_text')
  assert.equal(payload.baseFields.title, '公众号图文标题')
  assert.equal(payload.baseFields.noteContent, '公众号图文正文')
  assert.deepEqual(payload.baseFields.tags, ['公众号', '测试'])
  assert.deepEqual(payload.fileList, ['/media/cover.png', '/media/detail-1.png'])
  assert.deepEqual(payload.accountList, ['wechatmp_creator.json'])
})
