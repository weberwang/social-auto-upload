/**
 * 统一维护账号平台的展示名称、后端类型编号与标签样式。
 * 平台能力集中在这里维护，避免前端各处各写一套规则。
 */
export const ACCOUNT_PLATFORM_LABEL_BY_TYPE = {
  1: '小红书',
  2: '视频号',
  3: '抖音',
  4: '快手',
  5: 'B站',
  6: '微信公众号'
}

/**
 * 账号管理页的平台展示顺序。
 */
export const ACCOUNT_PLATFORM_LABELS = [
  '快手',
  '抖音',
  '视频号',
  '小红书',
  'B站',
  '微信公众号'
]

/**
 * 平台名称到历史 Web 类型编号的映射。
 */
export const ACCOUNT_PLATFORM_TYPE_BY_LABEL = {
  小红书: 1,
  视频号: 2,
  抖音: 3,
  快手: 4,
  B站: 5,
  微信公众号: 6
}

/**
 * 平台标签颜色映射，便于列表、概览卡片和说明页保持一致。
 */
export const ACCOUNT_PLATFORM_TAG_TYPE_MAP = {
  快手: 'success',
  抖音: 'danger',
  视频号: 'warning',
  小红书: 'info',
  B站: 'primary',
  微信公众号: 'success'
}

/**
 * 当前历史 Web 支持扫码登录的平台集合。
 */
export const ACCOUNT_PLATFORM_SSE_LOGIN_SUPPORTED_LABELS = new Set([
  '小红书',
  '视频号',
  '抖音',
  '快手',
  'B站',
  '微信公众号'
])
