/**
 * 全局 axios 实例：所有接口调用都从这里出去。
 *
 * 两个拦截器是重点：
 *   - 请求拦截器：自动加上 Authorization: Bearer <access>
 *   - 响应拦截器：access 过期（401）时自动用 refresh 换新的，然后重发原请求
 */
import axios from 'axios'

import { clearTokens, getAccess, getRefresh, setTokens } from './token'

// 开发环境读 .env.development（指向 http://127.0.0.1:8000/api），
// 打包后读 .env.production（用相对路径 /api，交给 Nginx 反向代理）
export const API_BASE_URL = import.meta.env.VITE_API_BASE_URL || '/api'

// 所有请求共用一个实例，超时、请求头、拦截器只配一次
const http = axios.create({
  baseURL: API_BASE_URL,
  timeout: 15000,
})

// ---------- 请求拦截器：出门前自动带上令牌 ----------
http.interceptors.request.use((config) => {
  // 每次请求都现读一次，这样 token 刷新后下一个请求立刻用上新的
  const access = getAccess()
  if (access) {
    config.headers.Authorization = `Bearer ${access}`
  }
  return config
})

// 同一时刻只刷新一次：其他 401 请求先 await 这个 Promise
let refreshPromise = null

function notifyExpired() {
  clearTokens()
  // 用自定义事件通知 App.vue 去清状态并跳转登录页，避免这里反向依赖 router
  window.dispatchEvent(new CustomEvent('auth:expired'))
}

// ---------- 响应拦截器：专门处理"登录过期" ----------
http.interceptors.response.use(
  (response) => response,
  async (error) => {
    const { config, response } = error
    const status = response?.status
    const url = config?.url || ''

    // 不是 401，或者已经重试过，就原样抛出
    // 登录接口自己的 401 是"密码错了"，不该触发刷新
    if (!config || status !== 401 || config._retry || url.includes('/auth/login')) {
      return Promise.reject(error)
    }

    // 本地没有 refresh，或者刷新的请求本身也 401 了，说明彻底过期
    const refresh = getRefresh()
    if (!refresh || url.includes('/auth/refresh')) {
      notifyExpired()
      return Promise.reject(error)
    }

    config._retry = true // 关键：打上标记，防止无限循环
    try {
      // 单飞：第一个 401 请求把刷新 Promise 存下来，其余请求直接复用它，
      // 避免十几个请求同时去换令牌（既浪费又容易被后端限流）
      refreshPromise =
        refreshPromise ||
        axios.post(`${API_BASE_URL}/auth/refresh/`, { refresh }).then((res) => res.data)
      const data = await refreshPromise
      refreshPromise = null

      // 写入新令牌，然后带着它把原来那个请求重发一遍
      setTokens({ access: data.access, refresh: data.refresh })
      config.headers = { ...config.headers, Authorization: `Bearer ${data.access}` }
      return http(config) // 带着新 token 重发原请求
    } catch (refreshError) {
      refreshPromise = null
      notifyExpired() // refresh 也过期了，只能重新登录
      return Promise.reject(refreshError)
    }
  },
)

// 页面里 import http from '@/api/http'，或者更常见的：用 './index.js' 里封装好的方法
export default http
