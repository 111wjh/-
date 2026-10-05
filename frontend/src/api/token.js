/**
 * token 的存取都收在这一个文件里，方便统一改名或换成别的存储方案。
 *
 * 说明：localStorage 简单好懂，但页面里任何 JS 都能读到，存在 XSS 风险；
 * 正式项目可以考虑 httpOnly Cookie + CSRF 的写法。
 */
const ACCESS_KEY = 'blog_access_token'
const REFRESH_KEY = 'blog_refresh_token'
const USER_KEY = 'blog_user'

// 读：请求拦截器每次发请求前都会调用 getAccess()
export const getAccess = () => localStorage.getItem(ACCESS_KEY)
export const getRefresh = () => localStorage.getItem(REFRESH_KEY)

// 写：登录成功、令牌刷新成功时调用；两个字段都是可选的
export function setTokens({ access, refresh } = {}) {
  if (access) localStorage.setItem(ACCESS_KEY, access)
  if (refresh) localStorage.setItem(REFRESH_KEY, refresh)
}

// 清空：退出登录、令牌彻底失效时调用
export function clearTokens() {
  localStorage.removeItem(ACCESS_KEY)
  localStorage.removeItem(REFRESH_KEY)
  localStorage.removeItem(USER_KEY)
}

// 用户资料也缓存一份，刷新页面时能立刻显示用户名，不用等接口返回
export function saveUser(user) {
  if (user) localStorage.setItem(USER_KEY, JSON.stringify(user))
  else localStorage.removeItem(USER_KEY)
}

// 注意 try/catch：localStorage 里的内容可能被用户或插件改坏，解析失败就当作没登录
export function loadUser() {
  try {
    return JSON.parse(localStorage.getItem(USER_KEY)) || null
  } catch {
    return null
  }
}
