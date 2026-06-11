import test from 'node:test'
import assert from 'node:assert/strict'

import { parseAccountLoginSseMessage } from '../src/composables/accountManagementSseMessage.js'

test('长调试日志不应被误判为二维码消息', () => {
  const logMessage = 'LOG:微信公众号:qr_ready:path=D:\\Git\\social-auto-upload\\cookiesFile\\wechatmp.png;payload_length=15230;image_bytes=11406'
  const parsed = parseAccountLoginSseMessage(logMessage, false)

  assert.equal(parsed.type, 'log')
  assert.equal(parsed.message, logMessage)
})

test('真正的 data:image 二维码应保留原始 src', () => {
  const qrMessage = 'data:image/png;base64,wechatmp-qrcode'
  const parsed = parseAccountLoginSseMessage(qrMessage, false)

  assert.equal(parsed.type, 'qrcode')
  assert.equal(parsed.src, qrMessage)
})

test('历史纯 base64 二维码消息应补全 data URL 前缀', () => {
  const qrMessage = 'a'.repeat(128)
  const parsed = parseAccountLoginSseMessage(qrMessage, false)

  assert.equal(parsed.type, 'qrcode')
  assert.equal(parsed.src, `data:image/png;base64,${qrMessage}`)
})
