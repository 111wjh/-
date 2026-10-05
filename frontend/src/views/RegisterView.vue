<!--
  注册页。
  和登录页几乎一样，区别是：前端先做一次"两次密码一致"的检查，
  真正的用户名唯一性、密码强度校验都交给后端（Django 自带的密码校验器）。
-->
<script setup>
import { reactive, ref } from 'vue'
import { useRouter } from 'vue-router'

import { useAuthStore } from '@/stores/auth'
import { errorMessage } from '@/utils/format'

const router = useRouter()
const auth = useAuthStore()

const form = reactive({
  username: '',
  email: '',
  password: '',
  password_confirm: '',
})
const error = ref('')

async function submit() {
  error.value = ''
  // 前端只做最基础的检查，错误提示能立刻出现，不用等一次网络往返
  if (form.password !== form.password_confirm) {
    error.value = '两次输入的密码不一致。'
    return
  }
  try {
    // 后端注册成功后会直接返回 token，所以这里注册完就是已登录状态
    await auth.register({ ...form })
    router.push({ name: 'home' })
  } catch (requestError) {
    // 用户名重复、密码太简单等错误都会走到这里，字段名 + 原因由 errorMessage 拼好
    error.value = errorMessage(requestError, '注册失败')
  }
}
</script>

<template>
  <div class="container container-narrow auth-page">
    <h1 class="section-title">注册</h1>
    <!-- 密码规则来自后端 settings.AUTH_PASSWORD_VALIDATORS，前端只是提前告知用户 -->
    <p class="muted">密码至少 8 位，不能是纯数字，也不能太简单（Django 自带强度校验）。</p>

    <form class="form-card" @submit.prevent="submit">
      <label class="field">
        <span>用户名</span>
        <input v-model.trim="form.username" type="text" autocomplete="username" required />
      </label>

      <label class="field">
        <span>邮箱（可不填）</span>
        <input v-model.trim="form.email" type="email" autocomplete="email" />
      </label>

      <label class="field">
        <span>密码</span>
        <input
          v-model="form.password"
          type="password"
          minlength="8"
          autocomplete="new-password"
          required
        />
      </label>

      <label class="field">
        <span>确认密码</span>
        <input
          v-model="form.password_confirm"
          type="password"
          minlength="8"
          autocomplete="new-password"
          required
        />
      </label>

      <p v-if="error" class="alert alert-error">{{ error }}</p>

      <button class="btn btn-primary btn-block" type="submit" :disabled="auth.loading">
        {{ auth.loading ? '注册中…' : '注册并登录' }}
      </button>

      <p class="muted center">
        已经有账号？<RouterLink :to="{ name: 'login' }">去登录</RouterLink>
      </p>
    </form>
  </div>
</template>
