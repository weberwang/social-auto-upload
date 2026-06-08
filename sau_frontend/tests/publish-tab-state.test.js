import test from 'node:test'
import assert from 'node:assert/strict'

import {
  copyPublishTabToPlatform,
  createDefaultPublishTabState,
  flattenPublishTabState,
  getPlatformEnhancementComponentName,
  migrateLegacyPublishTab
} from '../src/constants/publishTabState.js'
import {
  PUBLISH_CONTENT_TYPE_IMAGE_TEXT,
  PUBLISH_CONTENT_TYPE_VIDEO
} from '../src/constants/publishPlatforms.js'

/**
 * 构造统一状态模型测试数据，避免测试依赖页面运行时对象。
 */
function buildStateTab(overrides = {}) {
  const baseTab = createDefaultPublishTabState()
  return {
    ...baseTab,
    ...overrides,
    meta: {
      ...baseTab.meta,
      ...(overrides.meta || {})
    },
    platform: {
      ...baseTab.platform,
      ...(overrides.platform || {})
    },
    materials: {
      ...baseTab.materials,
      ...(overrides.materials || {})
    },
    accounts: {
      ...baseTab.accounts,
      ...(overrides.accounts || {})
    },
    baseFields: {
      ...baseTab.baseFields,
      ...(overrides.baseFields || {})
    },
    platformFields: {
      ...baseTab.platformFields,
      douyin: {
        ...baseTab.platformFields.douyin,
        ...(overrides.platformFields?.douyin || {})
      },
      kuaishou: {
        ...baseTab.platformFields.kuaishou,
        ...(overrides.platformFields?.kuaishou || {})
      },
      xiaohongshu: {
        ...baseTab.platformFields.xiaohongshu,
        ...(overrides.platformFields?.xiaohongshu || {})
      },
      tencent: {
        ...baseTab.platformFields.tencent,
        ...(overrides.platformFields?.tencent || {})
      },
      bilibili: {
        ...baseTab.platformFields.bilibili,
        ...(overrides.platformFields?.bilibili || {})
      }
    }
  }
}

test('旧 B站视频草稿恢复时应把简介迁移到 B站平台字段', () => {
  const migratedTab = migrateLegacyPublishTab({
    selectedPlatform: 5,
    contentType: PUBLISH_CONTENT_TYPE_VIDEO,
    description: 'B站简介',
    bilibiliTid: 17
  }, 0)

  assert.equal(migratedTab.platform.selectedPlatform, 5)
  assert.equal(migratedTab.baseFields.description, '')
  assert.equal(migratedTab.platformFields.bilibili.description, 'B站简介')
  assert.equal(migratedTab.platformFields.bilibili.tid, 17)
})

test('旧 B站视频草稿缺少分区时应保持空分区', () => {
  const migratedTab = migrateLegacyPublishTab({
    selectedPlatform: 5,
    contentType: PUBLISH_CONTENT_TYPE_VIDEO,
    description: 'B站简介',
    bilibiliTid: null
  }, 0)

  assert.equal(migratedTab.platformFields.bilibili.tid, null)
})

test('跨平台复制到仅支持视频的平台时应回退图文并清空正文和图片素材', () => {
  const copiedTab = copyPublishTabToPlatform(
    buildStateTab({
      platform: {
        selectedPlatform: 1,
        contentType: PUBLISH_CONTENT_TYPE_IMAGE_TEXT
      },
      materials: {
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
        ]
      },
      baseFields: {
        noteContent: '这是一条图文正文'
      }
    }),
    2,
    3
  )

  assert.equal(copiedTab.platform.contentType, PUBLISH_CONTENT_TYPE_VIDEO)
  assert.equal(copiedTab.baseFields.noteContent, '')
  assert.deepEqual(copiedTab.materials.fileList, [])
  assert.deepEqual(copiedTab.materials.displayFileList, [])
})

test('跨平台复制时应清空 B站、抖音和视频号的专属字段', () => {
  const copiedTab = copyPublishTabToPlatform(
    buildStateTab({
      platform: {
        selectedPlatform: 5,
        contentType: PUBLISH_CONTENT_TYPE_VIDEO
      },
      platformFields: {
        bilibili: {
          description: 'B站简介',
          tid: 17
        },
        douyin: {
          productTitle: '演示商品',
          productLink: 'https://example.com/item'
        },
        tencent: {
          isDraft: true
        }
      }
    }),
    1,
    4
  )

  assert.equal(copiedTab.platform.selectedPlatform, 1)
  assert.equal(copiedTab.platformFields.bilibili.description, '')
  assert.equal(copiedTab.platformFields.bilibili.tid, null)
  assert.equal(copiedTab.platformFields.douyin.productTitle, '')
  assert.equal(copiedTab.platformFields.douyin.productLink, '')
  assert.equal(copiedTab.platformFields.tencent.isDraft, false)
})

test('统一状态模型拍平成旧视图字段后应保留现有复制入口需要的结构', () => {
  const flattenedTab = flattenPublishTabState(
    buildStateTab({
      meta: {
        name: 'tab6'
      },
      platform: {
        selectedPlatform: 4
      },
      baseFields: {
        title: '统一状态标题',
        topics: ['新模型']
      }
    })
  )

  assert.equal(flattenedTab.name, 'tab6')
  assert.equal(flattenedTab.selectedPlatform, 4)
  assert.equal(flattenedTab.title, '统一状态标题')
  assert.deepEqual(flattenedTab.selectedTopics, ['新模型'])
})

test('视频号视频应挂载视频号视频增强组件', () => {
  assert.equal(
    getPlatformEnhancementComponentName(2, PUBLISH_CONTENT_TYPE_VIDEO),
    'TencentVideoEnhancement'
  )
})

test('视频号图文应挂载视频号图文增强组件', () => {
  assert.equal(
    getPlatformEnhancementComponentName(2, PUBLISH_CONTENT_TYPE_IMAGE_TEXT),
    'TencentImageTextEnhancement'
  )
})

test('B站视频应挂载 B站专属组件', () => {
  assert.equal(
    getPlatformEnhancementComponentName(5, PUBLISH_CONTENT_TYPE_VIDEO),
    'BilibiliPublishFields'
  )
})
