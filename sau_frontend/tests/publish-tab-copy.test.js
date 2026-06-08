import test from 'node:test'
import assert from 'node:assert/strict'

import {
  createCopiedPublishTab,
  createCopiedPublishTabsForPlatforms
} from '../src/constants/publishTabCopy.js'
import { migrateLegacyPublishTab } from '../src/constants/publishTabState.js'
import {
  PUBLISH_CONTENT_TYPE_IMAGE_TEXT,
  PUBLISH_CONTENT_TYPE_VIDEO
} from '../src/constants/publishPlatforms.js'

/**
 * 构造发布中心复制测试所需的最小 Tab 数据，避免测试被页面运行态字段干扰。
 */
function buildSourceTab(overrides = {}) {
  return {
    name: 'tab1',
    label: '发布1',
    fileList: [
      {
        name: 'clip-a.mp4',
        url: '/media/clip-a.mp4',
        path: '/media/clip-a.mp4',
        size: 1024,
        type: 'video/*'
      }
    ],
    displayFileList: [
      {
        name: 'clip-a.mp4',
        url: '/media/clip-a.mp4'
      }
    ],
    selectedAccounts: ['acct-1'],
    selectedPlatform: 1,
    contentType: PUBLISH_CONTENT_TYPE_VIDEO,
    title: '夏季上新',
    description: '',
    noteContent: '',
    bilibiliTid: null,
    productLink: '',
    productTitle: '',
    selectedTopics: ['新品', '测评'],
    scheduleEnabled: true,
    videosPerDay: 2,
    dailyTimes: ['10:00', '18:00'],
    startDays: 1,
    publishStatus: { message: '发布成功', type: 'success' },
    publishing: true,
    isDraft: false,
    isOriginal: true,
    ...overrides
  }
}

test('复制到支持当前内容类型的平台时应保留通用字段并重置运行态字段', () => {
  const copiedTab = createCopiedPublishTab(
    buildSourceTab(),
    3,
    2
  )

  assert.equal(copiedTab.name, 'tab2')
  assert.equal(copiedTab.label, '未选账号·抖音')
  assert.equal(copiedTab.selectedPlatform, 3)
  assert.equal(copiedTab.contentType, PUBLISH_CONTENT_TYPE_VIDEO)
  assert.equal(copiedTab.title, '夏季上新')
  assert.deepEqual(copiedTab.selectedTopics, ['新品', '测评'])
  assert.deepEqual(copiedTab.dailyTimes, ['10:00', '18:00'])
  assert.equal(copiedTab.scheduleEnabled, true)
  assert.equal(copiedTab.isOriginal, true)
  assert.deepEqual(copiedTab.selectedAccounts, [])
  assert.equal(copiedTab.publishStatus, null)
  assert.equal(copiedTab.publishing, false)
  assert.deepEqual(copiedTab.fileList.map((file) => file.name), ['clip-a.mp4'])
  assert.deepEqual(copiedTab.displayFileList, [
    {
      name: 'clip-a.mp4',
      url: '/media/clip-a.mp4'
    }
  ])
})

test('复制到仅支持视频的平台时应回退内容类型并清空不兼容字段', () => {
  const copiedTab = createCopiedPublishTab(
    buildSourceTab({
      fileList: [
        {
          name: 'cover-a.jpg',
          url: '/media/cover-a.jpg',
          path: '/media/cover-a.jpg',
          size: 2048,
          type: 'image/*'
        }
      ],
      displayFileList: [
        {
          name: 'cover-a.jpg',
          url: '/media/cover-a.jpg'
        }
      ],
      selectedPlatform: 1,
      contentType: PUBLISH_CONTENT_TYPE_IMAGE_TEXT,
      noteContent: '这是一条图文正文',
      isDraft: true
    }),
    2,
    3
  )

  assert.equal(copiedTab.name, 'tab3')
  assert.equal(copiedTab.label, '未选账号·视频号')
  assert.equal(copiedTab.selectedPlatform, 2)
  assert.equal(copiedTab.contentType, PUBLISH_CONTENT_TYPE_VIDEO)
  assert.equal(copiedTab.noteContent, '')
  assert.equal(copiedTab.isDraft, false)
  assert.deepEqual(copiedTab.fileList, [])
  assert.deepEqual(copiedTab.displayFileList, [])
})

test('复制到非平台专属能力页时应清空平台专属字段', () => {
  const copiedTab = createCopiedPublishTab(
    buildSourceTab({
      selectedPlatform: 5,
      description: 'B站简介',
      bilibiliTid: 17,
      productLink: 'https://example.com/item',
      productTitle: '演示商品',
      isDraft: true
    }),
    1,
    4
  )

  assert.equal(copiedTab.selectedPlatform, 1)
  assert.equal(copiedTab.description, '')
  assert.equal(copiedTab.bilibiliTid, null)
  assert.equal(copiedTab.productLink, '')
  assert.equal(copiedTab.productTitle, '')
  assert.equal(copiedTab.isDraft, false)
})

test('复制入口应兼容旧草稿迁移后的统一状态模型', () => {
  const migratedTab = migrateLegacyPublishTab(
    buildSourceTab({
      selectedPlatform: 5,
      description: 'B站简介',
      bilibiliTid: 17
    }),
    0
  )
  const copiedTab = createCopiedPublishTab(migratedTab, 5, 4)

  assert.equal(copiedTab.selectedPlatform, 5)
  assert.equal(copiedTab.description, 'B站简介')
  assert.equal(copiedTab.bilibiliTid, 17)
})

test('复制内容时不应带入未知运行态字段', () => {
  const copiedTab = createCopiedPublishTab(
    buildSourceTab({
      publishJobId: 'job-123',
      uploadSessionToken: 'secret-token',
      transientState: {
        locked: true
      }
    }),
    4,
    5
  )

  assert.equal('publishJobId' in copiedTab, false)
  assert.equal('uploadSessionToken' in copiedTab, false)
  assert.equal('transientState' in copiedTab, false)
})

test('同平台复制时应保留该平台专属字段', () => {
  const copiedTab = createCopiedPublishTab(
    buildSourceTab({
      selectedPlatform: 5,
      description: 'B站简介',
      bilibiliTid: 17
    }),
    5,
    6
  )

  assert.equal(copiedTab.selectedPlatform, 5)
  assert.equal(copiedTab.description, 'B站简介')
  assert.equal(copiedTab.bilibiliTid, 17)
})

test('复制全部平台时应为除当前平台外的其他平台批量创建新标签', () => {
  const copiedTabs = createCopiedPublishTabsForPlatforms(
    buildSourceTab({
      selectedPlatform: 1
    }),
    [3, 4, 2, 1, 5],
    2
  )

  assert.deepEqual(
    copiedTabs.map((tab) => ({
      name: tab.name,
      label: tab.label,
      selectedPlatform: tab.selectedPlatform
    })),
    [
      { name: 'tab2', label: '未选账号·抖音', selectedPlatform: 3 },
      { name: 'tab3', label: '未选账号·快手', selectedPlatform: 4 },
      { name: 'tab4', label: '未选账号·视频号', selectedPlatform: 2 },
      { name: 'tab5', label: '未选账号·B站', selectedPlatform: 5 }
    ]
  )
})
