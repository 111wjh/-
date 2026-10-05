<!--
  顶部导航栏。
  会用到的两个知识点：
    1. 直接读 Pinia store 里的登录状态，登录/未登录显示不同的按钮组
    2. <RouterLink> 通过路由名跳转，而不是写死 URL，改路径时只改 router 配置
-->
<script setup>
import { computed } from 'vue'
import { useRouter } from 'vue-router'

import { useAuthStore } from '@/stores/auth'

const auth = useAuthStore()
const router = useRouter()

// computed 是"由别的数据算出来"的数据，auth.access 变了它会自动更新
const isLoggedIn = computed(() => auth.isLoggedIn)

function logout() {
  // 只清前端保存的 token 和用户资料；JWT 是无状态的，服务端不需要通知
  auth.logout()
  router.push({ name: 'home' })
}
</script>

<template>
  <header class="site-header">
    <div class="container header-inner">
      <!-- 站点 Logo，点击回首页。:to 传对象比传字符串更安全，路由改名不会漏改 -->
      <RouterLink class="brand" :to="{ name: 'home' }">
        <span class="brand-mark">L</span>
        <span class="brand-text">
          <strong>学习日志</strong>
          <small>Learning Log</small>
        </span>
      </RouterLink>

      <!-- RouterLink 自动激活时会给当前页的链接加上 router-link-active 类，样式里直接用它高亮 -->
      <nav class="main-nav">
        <RouterLink :to="{ name: 'home' }">首页</RouterLink>
        <RouterLink :to="{ name: 'archive' }">归档</RouterLink>
        <RouterLink :to="{ name: 'about' }">关于</RouterLink>
      </nav>

      <div class="header-actions">
        <!-- v-if / v-else 决定渲染哪一组按钮；<template> 只是分组，不会生成多余标签 -->
        <RouterLink v-if="isLoggedIn" class="btn btn-primary btn-sm" :to="{ name: 'write' }">
          ✏️ 写文章
        </RouterLink>
        <template v-if="isLoggedIn">
          <RouterLink class="btn btn-ghost btn-sm" :to="{ name: 'dashboard' }">
            <!-- {{ }} 是插值语法，把 JS 表达式的值显示成文本 -->
            {{ auth.username }} 的文章
          </RouterLink>
          <button class="btn btn-ghost btn-sm" type="button" @click="logout">退出</button>
        </template>
        <template v-else>
          <RouterLink class="btn btn-ghost btn-sm" :to="{ name: 'login' }">登录</RouterLink>
          <RouterLink class="btn btn-primary btn-sm" :to="{ name: 'register' }">注册</RouterLink>
        </template>
      </div>
    </div>
  </header>
</template>
