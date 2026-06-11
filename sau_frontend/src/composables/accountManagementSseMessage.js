/**
 * 判断账号登录 SSE 消息类型，并在需要时生成二维码可直接展示的 src。
 */
export function parseAccountLoginSseMessage(data, hasQrCodeData = false) {
  if (typeof data !== 'string') {
    return { type: 'unknown', raw: data }
  }

  if (data.startsWith('SESSION:')) {
    return {
      type: 'session',
      sessionId: data.slice('SESSION:'.length).trim(),
      raw: data
    }
  }

  if (data.startsWith('LOG:')) {
    return { type: 'log', message: data, raw: data }
  }

  if (data.startsWith('ERROR:')) {
    return {
      type: 'error',
      message: data.slice('ERROR:'.length).trim(),
      raw: data
    }
  }

  if (data === 'CANCELLED') {
    return { type: 'cancelled', raw: data }
  }

  if (data === '200' || data === '500') {
    return {
      type: 'terminal',
      status: data,
      raw: data
    }
  }

  if (!hasQrCodeData && data.startsWith('data:image/')) {
    return {
      type: 'qrcode',
      src: data,
      raw: data
    }
  }

  // 二维码消息必须晚于控制消息判断，避免长日志被误拼成 data URL 导致前端显示坏图。
  if (!hasQrCodeData && data.length > 100) {
    return {
      type: 'qrcode',
      src: `data:image/png;base64,${data}`,
      raw: data
    }
  }

  return { type: 'unknown', raw: data }
}
