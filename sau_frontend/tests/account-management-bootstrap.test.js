import test from 'node:test'
import assert from 'node:assert/strict'

import { bootstrapAccountManagementPage } from '../src/composables/accountManagementBootstrap.js'

test('首次进入账号页时应快速加载并触发后台校验', async () => {
  const calls = []

  await bootstrapAccountManagementPage({
    isFirstVisit: true,
    hasCachedAccounts: false,
    fetchAccountsQuick: async () => {
      calls.push('quick')
    },
    validateAllAccountsInBackground: () => {
      calls.push('validate')
    }
  })

  assert.deepEqual(calls, ['quick', 'validate'])
})

test('再次进入账号页且已有缓存时不应自动刷新', async () => {
  const calls = []

  await bootstrapAccountManagementPage({
    isFirstVisit: false,
    hasCachedAccounts: true,
    fetchAccountsQuick: async () => {
      calls.push('quick')
    },
    validateAllAccountsInBackground: () => {
      calls.push('validate')
    }
  })

  assert.deepEqual(calls, [])
})

test('再次进入账号页但缓存为空时只应快速加载本地列表', async () => {
  const calls = []

  await bootstrapAccountManagementPage({
    isFirstVisit: false,
    hasCachedAccounts: false,
    fetchAccountsQuick: async () => {
      calls.push('quick')
    },
    validateAllAccountsInBackground: () => {
      calls.push('validate')
    }
  })

  assert.deepEqual(calls, ['quick'])
})
