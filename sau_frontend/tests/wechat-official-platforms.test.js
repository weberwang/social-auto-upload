import test from 'node:test'
import assert from 'node:assert/strict'

import {
  ACCOUNT_PLATFORM_LABEL_BY_TYPE,
  ACCOUNT_PLATFORM_SSE_LOGIN_SUPPORTED_LABELS,
  ACCOUNT_PLATFORM_TYPE_BY_LABEL
} from '../src/constants/accountPlatforms.js'
import {
  PUBLISH_CONTENT_TYPE_IMAGE_TEXT,
  PUBLISH_CONTENT_TYPE_VIDEO,
  PUBLISH_PLATFORM_OPTIONS,
  getPublishPlatformOption,
  isContentTypeSupportedForPlatform
} from '../src/constants/publishPlatforms.js'

test('账号平台常量应包含微信公众号映射', () => {
  assert.equal(ACCOUNT_PLATFORM_LABEL_BY_TYPE[6], '微信公众号')
  assert.equal(ACCOUNT_PLATFORM_TYPE_BY_LABEL.微信公众号, 6)
  assert.equal(ACCOUNT_PLATFORM_SSE_LOGIN_SUPPORTED_LABELS.has('微信公众号'), true)
})

test('发布平台常量应声明微信公众号只支持图文', () => {
  const platform = getPublishPlatformOption(6)

  assert.ok(PUBLISH_PLATFORM_OPTIONS.some((item) => item.key === 6))
  assert.equal(platform?.name, '微信公众号')
  assert.equal(isContentTypeSupportedForPlatform(6, PUBLISH_CONTENT_TYPE_IMAGE_TEXT), true)
  assert.equal(isContentTypeSupportedForPlatform(6, PUBLISH_CONTENT_TYPE_VIDEO), false)
})
