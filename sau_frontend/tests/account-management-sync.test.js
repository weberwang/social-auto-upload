import test from 'node:test'
import assert from 'node:assert/strict'

import { createAccountFetchCoordinator } from '../src/composables/accountFetchCoordinator.js'

/**
 * 创建一个可手动控制完成时机的 Promise，便于稳定复现并发请求乱序返回。
 */
function createDeferred() {
  let resolve
  const promise = new Promise((resolver) => {
    resolve = resolver
  })

  return { promise, resolve }
}

test('账号列表同步应忽略旧请求结果，保留最新返回的数据', async () => {
  const firstValidated = createDeferred()
  const secondValidated = createDeferred()
  const appliedPayloads = []
  const refreshingStates = []
  let validatedCallCount = 0

  const coordinator = createAccountFetchCoordinator({
    loadValidatedAccounts: async () => {
      validatedCallCount += 1
      return validatedCallCount === 1
        ? firstValidated.promise
        : secondValidated.promise
    },
    applyAccounts: (accounts) => {
      appliedPayloads.push(accounts.map((item) => item[3]))
    },
    setRefreshing: (status) => {
      refreshingStates.push(status)
    }
  })

  const firstRequest = coordinator.fetchValidatedAccounts({ silent: true })
  const secondRequest = coordinator.fetchValidatedAccounts({ silent: true, force: true })

  secondValidated.resolve({
    code: 200,
    data: [[2, 3, 'new-cookie.json', '新账号', 1]]
  })
  await secondRequest

  firstValidated.resolve({
    code: 200,
    data: [[1, 3, 'old-cookie.json', '旧账号', 1]]
  })
  await firstRequest

  assert.deepEqual(appliedPayloads, [['新账号']])
  assert.equal(refreshingStates.at(-1), false)
})
