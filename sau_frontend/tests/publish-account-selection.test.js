import test from 'node:test'
import assert from 'node:assert/strict'

import {
  getDefaultSelectedAccountIdsForPlatform
} from '../src/constants/publishPlatforms.js'

/**
 * 构造发布中心账号下拉测试数据，覆盖同平台多账号和跨平台过滤场景。
 */
function buildAccounts() {
  return [
    { id: 'xhs-1', name: '小红书主号', platform: '小红书' },
    { id: 'xhs-2', name: '小红书备用', platform: '小红书' },
    { id: 'dy-1', name: '抖音主号', platform: '抖音' }
  ]
}

test('当前平台无已选账号时应默认选中第一个可用账号', () => {
  assert.deepEqual(
    getDefaultSelectedAccountIdsForPlatform(buildAccounts(), [], 1),
    ['xhs-1']
  )
})

test('当前平台已有合法选中账号时应保留该账号', () => {
  assert.deepEqual(
    getDefaultSelectedAccountIdsForPlatform(buildAccounts(), ['xhs-2'], 1),
    ['xhs-2']
  )
})

test('当前平台没有账号时应返回空数组', () => {
  assert.deepEqual(
    getDefaultSelectedAccountIdsForPlatform(buildAccounts(), [], 2),
    []
  )
})

test('当前平台存在多个旧选中账号时应只保留第一个合法账号', () => {
  assert.deepEqual(
    getDefaultSelectedAccountIdsForPlatform(buildAccounts(), ['xhs-2', 'xhs-1'], 1),
    ['xhs-2']
  )
})
