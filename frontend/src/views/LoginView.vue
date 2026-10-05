<!--
  登录页。
  流程：表单 → auth.login()（内部调 /api/auth/login/）→ token 存本地 → 跳回原来想去的页面。
-->
<script setup>
import { reactive, ref } from 'vue'
import { useRoute, useRouter } from 'vue-router'

import { useAuthStore } from '@/stores/auth'
import { errorMessage } from '@/utils/format'

const route = useRoute()
const router = useRouter()
const auth = useAuthStore()

// reactive 适合"一个固定形状的对象"，表单字段都在这一个对象里，不用写 4 个 ref
const form = reactive({ username: '', password: '' })
const error = ref('')

async function submit() {
  error.value = ''
  try {
    // 展开成 { ...form } 是为了传一个普通对象副本给 store，避免外部直接改到表单
    await auth.login({ ...form })
    // 登录前想去哪，登录后就回哪
    router.push(String(route.query.redirect || '/'))
  } catch (requestError) {
    // 用户名或密码错误时，后端返回的是 401 + detail 字段，errorMessage 会把它翻出来
    error.value = errorMessage(requestError, '登录失败')
  }
}

/** 学习项目专用：一键填入演示账号，省得每次手打 */
function fillDemo() {
  form.username = 'demo'
  form.password = 'demo12345'
}
</script>

<template>
  <div class="container container-narrow auth-page">
    <h1 class="section-title">登录</h1>
    <p class="muted">
      演示账号：<code>demo / demo12345</code>
      <button class="link-button" type="button" @click="fillDemo">一键填入</button>
    </p>

    <!-- @submit.prevent 阻止浏览器默认的整页提交，改为由 submit() 处理 -->
    <form class="form-card" @submit.prevent="submit">
      <label class="field">
        <span>用户名</span>
        <!-- v-model.trim 会自动去掉首尾空格；autocomplete 让浏览器能记住密码 -->
        <input v-model.trim="form.username" type="text" autocomplete="username" required />
      </label>

      <label class="field">
        <span>密码</span>
        <input
          v-model="form.password"
          type="password"
          autocomplete="current-password"
          required
        />
      </label>

      <p v-if="error" class="alert alert-error">{{ error }}</p>

      <!-- auth.loading 是 store 里的状态：请求期间按钮变灰并显示"登录中…"，防止连点 -->
      <button class="btn btn-primary btn-block" type="submit" :disabled="auth.loading">
        {{ auth.loading ? '登录中…' : '登录' }}
      </button>

      <p class="muted center">
        还没有账号？<RouterLink :to="{ name: 'register' }">注册一个</RouterLink>
      </p>
    </form>
  </div>
</template>
