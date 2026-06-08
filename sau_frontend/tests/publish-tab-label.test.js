import test from 'node:test'
import assert from 'node:assert/strict'

import {
  buildPublishTabLabel,
  createDefaultPublishTab
} from '../src/constants/publishPlatforms.js'

/**
 * 构造账号列表测试数据，覆盖单账号、多账号和未知账号回退场景。
 */
function buildAccounts() {
  return [
    { id: 'acct-1', name: '主账号', platform: '抖音' },
    { id: 'acct-2', name: '分账号', platform: '抖音' }
  ]
}

test('未选择账号时页签标题应显示未选账号和平台名', () => {
  assert.equal(buildPublishTabLabel(3, [], buildAccounts()), '未选账号·抖音')
})

test('选择单个账号时页签标题应显示账号名和平台名', () => {
  assert.equal(buildPublishTabLabel(3, ['acct-1'], buildAccounts()), '主账号·抖音')
})

test('选择多个账号时页签标题应显示首个账号和数量', () => {
  assert.equal(buildPublishTabLabel(3, ['acct-1', 'acct-2'], buildAccounts()), '主账号等2个·抖音')
})

test('默认发布标签应使用账号与平台格式标题', () => {
  assert.equal(createDefaultPublishTab().label, '未选账号·小红书')
})
