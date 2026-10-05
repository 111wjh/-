<!--
  "我的文章"页：登录后管理自己的内容。
  上半部分能改个人资料，下半部分是文章表格（草稿也会列出来）。
  这个页面在 router 里标了 meta.requiresAuth，没登录进不来。
-->
<script setup>
import { onMounted, reactive, ref } from 'vue'

import { postsApi } from '@/api'
import { useAuthStore } from '@/stores/auth'
import { compactNumber, errorMessage, formatDate } from '@/utils/format'

const auth = useAuthStore()

const posts = ref([]) // 我的文章（含草稿）
const loading = ref(true)
const error = ref('')

// 个人资料表单，进页面时用当前用户信息回填
const profile = reactive({ email: '', first_name: '', last_name: '' })
const savingProfile = ref(false)
const profileMessage = ref('')

/** 拉取"我的文章" */
async function loadMine() {
  loading.value = true
  error.value = ''
  try {
    // mine=1 是后端的约定：带上自己的 token 就能看到草稿
    const data = await postsApi.list({ mine: 1, page_size: 50, ordering: '-updated_at' })
    posts.value = data.results
  } catch (requestError) {
    error.value = errorMessage(requestError)
  } finally {
    loading.value = false
  }
}

async function remove(post) {
  if (!window.confirm(`确定删除《${post.title}》吗？`)) return
  try {
    await postsApi.remove(post.slug)
    // 删除成功后从表格里移除这一行，不用整页重新加载
    posts.value = posts.value.filter((item) => item.id !== post.id)
  } catch (requestError) {
    error.value = errorMessage(requestError)
  }
}

async function saveProfile() {
  savingProfile.value = true
  profileMessage.value = ''
  try {
    await auth.updateProfile({ ...profile })
    profileMessage.value = '资料已更新。'
  } catch (requestError) {
    profileMessage.value = errorMessage(requestError)
  } finally {
    savingProfile.value = false
  }
}

onMounted(async () => {
  // 先刷新一次用户资料（可能在其他地方改过），再回填表单、加载文章
  await auth.fetchMe()
  if (auth.user) {
    profile.email = auth.user.email || ''
    profile.first_name = auth.user.first_name || ''
    profile.last_name = auth.user.last_name || ''
  }
  loadMine()
})
</script>

<template>
  <div class="container">
    <div class="section-head">
      <h2 class="section-title">我的文章</h2>
      <RouterLink class="btn btn-primary btn-sm" :to="{ name: 'write' }">✏️ 写新文章</RouterLink>
    </div>

    <!-- 资料卡片：PATCH /api/auth/me/ 只改传过去的字段 -->
    <section class="profile-card">
      <div>
        <p class="profile-name">{{ auth.user?.username }}</p>
        <p class="muted">
          已发布 {{ auth.user?.post_count ?? 0 }} 篇 ·
          注册于 {{ formatDate(auth.user?.date_joined) }}
        </p>
      </div>
      <form class="profile-form" @submit.prevent="saveProfile">
        <input v-model.trim="profile.email" type="email" placeholder="邮箱" />
        <input v-model.trim="profile.first_name" type="text" placeholder="名" />
        <input v-model.trim="profile.last_name" type="text" placeholder="姓" />
        <button class="btn btn-ghost btn-sm" type="submit" :disabled="savingProfile">
          保存资料
        </button>
      </form>
      <p v-if="profileMessage" class="muted">{{ profileMessage }}</p>
    </section>

    <p v-if="error" class="alert alert-error">{{ error }}</p>
    <p v-if="loading" class="muted">加载中…</p>
    <p v-else-if="!posts.length" class="empty-state">
      还没有文章，<RouterLink :to="{ name: 'write' }">开始写第一篇</RouterLink>吧。
    </p>

    <!-- 表格：每一行是一篇文章，状态列区分草稿和已发布 -->
    <table v-else class="post-table">
      <thead>
        <tr>
          <th>标题</th>
          <th>状态</th>
          <th>阅读</th>
          <th>评论</th>
          <th>更新时间</th>
          <th>操作</th>
        </tr>
      </thead>
      <tbody>
        <tr v-for="post in posts" :key="post.id">
          <td>
            <RouterLink :to="{ name: 'post', params: { slug: post.slug } }">
              {{ post.title }}
            </RouterLink>
          </td>
          <td>
            <!-- 三目运算符按状态给不同的样式类 -->
            <span class="chip" :class="post.status === 'draft' ? 'chip-draft' : 'chip-published'">
              {{ post.status === 'draft' ? '草稿' : '已发布' }}
            </span>
          </td>
          <td>{{ compactNumber(post.views) }}</td>
          <td>{{ post.comment_count }}</td>
          <td>{{ formatDate(post.updated_at, true) }}</td>
          <td class="row-actions">
            <RouterLink class="link-button" :to="{ name: 'edit', params: { slug: post.slug } }">
              编辑
            </RouterLink>
            <button class="link-danger" type="button" @click="remove(post)">删除</button>
          </td>
        </tr>
      </tbody>
    </table>
  </div>
</template>
