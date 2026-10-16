// 统一 fetch 封装：JSON 头、错误统一弹 Toast
import { showToast } from '../stores/toast'

async function request(method, url, body) {
  const opts = { method, headers: {} }
  if (body !== undefined) {
    opts.headers['Content-Type'] = 'application/json'
    opts.body = JSON.stringify(body)
  }

  let res
  try {
    res = await fetch('/api' + url, opts)
  } catch {
    showToast('网络错误，请检查服务是否在运行', 'error')
    throw new Error('network error')
  }

  let data = null
  try {
    data = await res.json()
  } catch {
    /* 非 JSON 响应（如文件下载之外的空体） */
  }

  if (!res.ok) {
    const msg = formatError(res.status, data)
    showToast(msg, 'error')
    throw new Error(msg)
  }
  return data
}

function formatError(status, data) {
  const d = data && data.detail
  if (typeof d === 'string') return d
  if (Array.isArray(d) && d.length) {
    // FastAPI 422 校验错误取第一条
    const first = d[0]
    return first.msg ? `参数错误：${first.msg}` : '参数错误'
  }
  if (status === 404) return '资源不存在'
  if (status === 422) return '参数校验失败'
  return `请求失败（${status}）`
}

export const api = {
  get: (url) => request('GET', url),
  post: (url, body) => request('POST', url, body),
  put: (url, body) => request('PUT', url, body),
  del: (url) => request('DELETE', url),
}

// 日期工具
export function todayStr() {
  const d = new Date()
  return `${d.getFullYear()}-${pad(d.getMonth() + 1)}-${pad(d.getDate())}`
}

export function pad(n) {
  return String(n).padStart(2, '0')
}

export function addDays(dateStr, delta) {
  const d = new Date(dateStr + 'T00:00:00')
  d.setDate(d.getDate() + delta)
  return `${d.getFullYear()}-${pad(d.getMonth() + 1)}-${pad(d.getDate())}`
}

export function formatDateCN(dateStr) {
  const d = new Date(dateStr + 'T00:00:00')
  const week = ['日', '一', '二', '三', '四', '五', '六'][d.getDay()]
  const today = todayStr()
  if (dateStr === today) return `今天 · ${d.getMonth() + 1}月${d.getDate()}日 周${week}`
  if (dateStr === addDays(today, 1)) return `明天 · ${d.getMonth() + 1}月${d.getDate()}日 周${week}`
  if (dateStr === addDays(today, -1)) return `昨天 · ${d.getMonth() + 1}月${d.getDate()}日 周${week}`
  return `${d.getMonth() + 1}月${d.getDate()}日 周${week}`
}

export function formatDatePlain(dateStr) {
  const d = new Date(dateStr + 'T00:00:00')
  return `${d.getMonth() + 1}/${d.getDate()}`
}
