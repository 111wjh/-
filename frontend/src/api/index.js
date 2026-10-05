/**
 * 接口清单：把"后端提供什么"在前端也写清楚，页面里只调用这些方法，不直接写 URL。
 *
 * 这么做的三个好处：
 *   1. 改接口地址时只改这一个文件
 *   2. 页面代码里出现的是 postsApi.list() 这种有语义的名字，可读性好
 *   3. 请求细节（超时、令牌、错误格式）统一由 http.js 负责
 */
import http from './http'

// slug 可能是中文，直接拼进 URL 会出问题，统一交给 encodeURIComponent 转义
const encode = (slug) => encodeURIComponent(slug)

export const postsApi = {
  /** 列表：支持 page / page_size / category / tag / author / search / year / month / ordering / mine */
  list(params = {}) {
    // get 的第二个参数是查询字符串，axios 会把它拼成 ?page=1&page_size=6
    return http.get('/posts/', { params }).then((res) => res.data)
  },
  /** 文章详情（阅读量会在后端 +1） */
  get(slug) {
    return http.get(`/posts/${encode(slug)}/`).then((res) => res.data)
  },
  /** 首页置顶推荐，后端做了切片，最多返回 5 条 */
  featured() {
    return http.get('/posts/featured/').then((res) => res.data)
  },
  /** 新建文章：payload 可以是普通对象，也可以是带文件的 FormData */
  create(payload) {
    return http.post('/posts/', payload).then((res) => res.data)
  },
  /** 修改用 PATCH（只传要改的字段），而不是 PUT（要传全部字段） */
  update(slug, payload) {
    return http.patch(`/posts/${encode(slug)}/`, payload).then((res) => res.data)
  },
  remove(slug) {
    return http.delete(`/posts/${encode(slug)}/`).then((res) => res.data)
  },
  /** 某篇文章的评论列表（带分页） */
  comments(slug, params = {}) {
    return http.get(`/posts/${encode(slug)}/comments/`, { params }).then((res) => res.data)
  },
  /** 发表评论：作者由后端从令牌里取，前端传不了也不该传 */
  addComment(slug, content) {
    return http
      .post(`/posts/${encode(slug)}/comments/`, { content })
      .then((res) => res.data)
  },
}

// 分类 / 标签 / 归档：首页右侧栏用得到的三组"标签体系"数据
export const taxonomyApi = {
  categories() {
    return http.get('/categories/', { params: { page_size: 50 } }).then((res) => res.data)
  },
  tags() {
    return http.get('/tags/', { params: { page_size: 50 } }).then((res) => res.data)
  },
  archive() {
    return http.get('/archive/').then((res) => res.data)
  },
}

// 认证相关：登录、注册、当前用户
export const authApi = {
  login(credentials) {
    return http.post('/auth/login/', credentials).then((res) => res.data)
  },
  /** 注册成功后后端直接返回 token，所以注册完就是登录状态 */
  register(payload) {
    return http.post('/auth/register/', payload).then((res) => res.data)
  },
  /** 取当前登录用户，用来验证令牌是否还有效 */
  me() {
    return http.get('/auth/me/').then((res) => res.data)
  },
  updateMe(payload) {
    return http.patch('/auth/me/', payload).then((res) => res.data)
  },
}

// 评论的删除单独走一个接口，因为它的地址不带文章 slug
export const commentsApi = {
  remove(id) {
    return http.delete(`/comments/${id}/`).then((res) => res.data)
  },
}
