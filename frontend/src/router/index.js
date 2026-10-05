/**
 * 前端路由表：网址 → 页面组件。
 *
 * 两个要点：
 *   1. component 都写成 () => import(...)，这叫懒加载 ——
 *      只有真的访问那个页面才下载对应的 JS，首页能更快打开
 *   2. meta 里放"这个页面需要什么权限"，由最下面的守卫统一判断
 */
import { createRouter, createWebHistory } from 'vue-router'

import { useAuthStore } from '@/stores/auth'

const routes = [
  // 首页：文章列表，支持 ?category= / ?tag= / ?search= 等查询参数
  { path: '/', name: 'home', component: () => import('@/views/HomeView.vue') },
  {
    path: '/posts/:slug',
    name: 'post',
    component: () => import('@/views/PostDetailView.vue'),
    // props: true 会把 :slug 当作 props 传给组件，组件里就不用写 useRoute()
    props: true,
  },
  { path: '/archive', name: 'archive', component: () => import('@/views/ArchiveView.vue') },
  { path: '/about', name: 'about', component: () => import('@/views/AboutView.vue') },
  // guestOnly：已经登录的人不该再看到登录/注册页
  {
    path: '/login',
    name: 'login',
    component: () => import('@/views/LoginView.vue'),
    meta: { guestOnly: true },
  },
  {
    path: '/register',
    name: 'register',
    component: () => import('@/views/RegisterView.vue'),
    meta: { guestOnly: true },
  },
  {
    path: '/write',
    name: 'write',
    component: () => import('@/views/EditorView.vue'),
    // requiresAuth：必须在登录状态下才能进
    meta: { requiresAuth: true },
  },
  {
    path: '/write/:slug',
    name: 'edit',
    component: () => import('@/views/EditorView.vue'),
    props: true,
    meta: { requiresAuth: true },
  },
  {
    path: '/me',
    name: 'dashboard',
    component: () => import('@/views/DashboardView.vue'),
    meta: { requiresAuth: true },
  },
  {
    // :pathMatch(.*)* 是通配写法，匹配所有前面没命中的地址（404 页）
    path: '/:pathMatch(.*)*',
    name: 'not-found',
    component: () => import('@/views/NotFoundView.vue'),
  },
]

const router = createRouter({
  // createWebHistory 用浏览器原生地址（没有 #），需要服务器把所有路径都指回 index.html
  history: createWebHistory(),
  routes,
  // 换页面时回到顶部；浏览器的后退前进仍然保留滚动位置
  scrollBehavior(to, from, savedPosition) {
    // savedPosition 是浏览器记录的上次位置，用后退键时优先恢复它
    return savedPosition || { top: 0 }
  },
})

// 前端路由守卫：只是"体验层"的拦截，真正的权限仍然由后端说了算
router.beforeEach((to) => {
  const auth = useAuthStore()
  // 返回一个路由对象 = 改去别处；返回 true = 放行
  if (to.meta.requiresAuth && !auth.isLoggedIn) {
    // 把想去的地址记在 ?redirect= 上，登录成功后自动跳回去
    return { name: 'login', query: { redirect: to.fullPath } }
  }
  if (to.meta.guestOnly && auth.isLoggedIn) {
    return { name: 'home' }
  }
  return true
})

export default router
