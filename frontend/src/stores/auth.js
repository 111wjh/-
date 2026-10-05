/** 登录状态：token 存本地，用户资料存 Pinia（内存），刷新页面时先读缓存再向后端核对。 */
import { defineStore } from 'pinia'

import { authApi } from '@/api'
import {
  clearTokens,
  getAccess,
  getRefresh,
  loadUser,
  saveUser,
  setTokens,
} from '@/api/token'

export const useAuthStore = defineStore('auth', {
  // state：仓库里的数据。token 从 localStorage 读，所以刷新页面登录状态不丢
  state: () => ({
    access: getAccess(),
    refresh: getRefresh(),
    user: loadUser(),
    loading: false,
  }),

  // getters：由 state 推导出来的值，等价于"带缓存的 computed"
  getters: {
    isLoggedIn: (state) => Boolean(state.access),
    username: (state) => state.user?.username || '',
    isStaff: (state) => Boolean(state.user?.is_staff),
  },

  // actions：在这里改 state、调接口。组件只调用 action，不直接改 state
  actions: {
    /** 登录/注册成功后统一处理：存 token + 记用户资料 */
    setSession(payload) {
      setTokens(payload)
      // setTokens 写的是 localStorage，这里同步更新内存里的 state
      this.access = getAccess()
      this.refresh = getRefresh()
      this.user = payload.user || this.user
      saveUser(this.user)
    },

    async login(credentials) {
      this.loading = true
      try {
        const data = await authApi.login(credentials)
        this.setSession(data)
        return data.user
      } finally {
        this.loading = false
      }
    },

    async register(payload) {
      this.loading = true
      try {
        const data = await authApi.register(payload)
        this.setSession(data)
        return data.user
      } finally {
        this.loading = false
      }
    },

    /** 刷新页面后拿最新的用户资料；顺带验证 token 是否还有效 */
    async fetchMe() {
      // 压根没登录就别发请求了
      if (!this.access) return null
      try {
        const user = await authApi.me()
        this.user = user
        saveUser(user)
        return user
      } catch {
        // 拦截器会处理 401；这里只做兜底，不让页面报错
        return null
      }
    },

    /** 改昵称、邮箱等（"我的文章"页用到） */
    async updateProfile(payload) {
      const user = await authApi.updateMe(payload)
      this.user = user
      saveUser(user)
      return user
    },

    /** 退出：清 localStorage + 清内存状态。JWT 无状态，服务端不用通知 */
    logout() {
      clearTokens()
      this.access = null
      this.refresh = null
      this.user = null
    },
  },
})
