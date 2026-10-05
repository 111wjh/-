/**
 * 展示层用的小工具函数。
 * 放在这里而不是写在组件里，是因为它们会被多个页面复用，
 * 集中一份也方便统一修改（比如以后日期要带秒，只改这里）。
 */

/** 把接口返回的 ISO 时间格式化成 2026-09-25 / 2026-09-25 14:46 */
export function formatDate(value, withTime = false) {
  if (!value) return ''
  const date = new Date(value)
  if (Number.isNaN(date.getTime())) return '' // 时间字符串不合法时不显示"Invalid Date"
  const pad = (num) => String(num).padStart(2, '0')
  const base = `${date.getFullYear()}-${pad(date.getMonth() + 1)}-${pad(date.getDate())}`
  return withTime ? `${base} ${pad(date.getHours())}:${pad(date.getMinutes())}` : base
}

/** 相对时间：刚刚 / 5 分钟前 / 3 天前，超过 30 天就直接显示日期 */
export function relativeTime(value) {
  if (!value) return ''
  const diff = Date.now() - new Date(value).getTime()
  const minute = 60 * 1000
  const hour = 60 * minute
  const day = 24 * hour

  if (diff < minute) return '刚刚'
  if (diff < hour) return `${Math.floor(diff / minute)} 分钟前`
  if (diff < day) return `${Math.floor(diff / hour)} 小时前`
  if (diff < 30 * day) return `${Math.floor(diff / day)} 天前`
  return formatDate(value)
}

/** 阅读时长：后端算好了分钟数，这里只负责措辞 */
export function readingTime(minutes) {
  return `约 ${minutes || 1} 分钟`
}

/** 大数字缩写：1234 → 1.2k，12345 → 1.2w */
export function compactNumber(value) {
  const num = Number(value) || 0
  if (num < 1000) return String(num)
  if (num < 10000) return `${(num / 1000).toFixed(1)}k`
  return `${(num / 10000).toFixed(1)}w`
}

/**
 * 把接口返回的错误变成一句人话。
 *
 * DRF 的报错长这样：{ "title": ["这个字段是必填项。"], "detail": "..." }
 */
export function errorMessage(error, fallback = '请求失败，请稍后再试') {
  if (!error) return fallback
  if (error.code === 'ECONNABORTED') return '请求超时，请检查网络。'
  if (error.message === 'Network Error') {
    return '连不上后端服务，请确认 Django 已启动（127.0.0.1:8000）。'
  }

  const data = error.response?.data
  if (!data) return error.message || fallback
  if (typeof data === 'string') return data
  if (data.detail) return data.detail

  const messages = Object.entries(data).map(([field, value]) => {
    const text = Array.isArray(value) ? value.join(' ') : String(value)
    return field === 'non_field_errors' ? text : `${field}：${text}`
  })
  return messages.join('；') || fallback
}
