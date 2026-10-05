<!--
  根组件：整个站点的"外壳"。
  结构很简单 —— 顶部导航 + 中间的页面出口（<RouterView />）+ 页脚，
  换页面时只有 <RouterView /> 里的内容会被替换。
-->
<script setup>
import { onMounted, onUnmounted } from 'vue'
import { useRouter } from 'vue-router'

import SiteFooter from '@/components/SiteFooter.vue'
import SiteHeader from '@/components/SiteHeader.vue'
import { useAuthStore } from '@/stores/auth'

// useRouter() 拿到全局路由对象，用来在代码里跳转页面
const router = useRouter()
// useAuthStore() 拿到登录状态的仓库（Pinia store），任何组件都能读它
const auth = useAuthStore()

// token 彻底失效（refresh 也过期）时，http.js 会广播这个事件
function handleExpired() {
  // 1) 清掉本地登录状态  2) 跳到登录页，并把当前地址记下来，登录后能跳回来
  auth.logout()
  router.push({ name: 'login', query: { redirect: router.currentRoute.value.fullPath } })
}

onMounted(() => {
  // 监听 token 失效事件；组件卸载时要记得移除监听，否则会重复绑定
  window.addEventListener('auth:expired', handleExpired)
  auth.fetchMe() // 刷新页面后核对一次登录状态
})

onUnmounted(() => window.removeEventListener('auth:expired', handleExpired))
</script>

<template>
  <div class="app-shell">
    <SiteHeader />
    <main class="app-main">
      <!-- 当前路由匹配到的页面组件会渲染在这里 -->
      <RouterView />
    </main>
    <SiteFooter />
  </div>
</template>
