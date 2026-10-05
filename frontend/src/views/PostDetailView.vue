<!--
  文章详情页。
  props.slug 来自路由配置里的 props: true，也就是网址中的 /posts/<slug> 那一段。
  页面本身负责三件事：请求正文、按权限显示编辑/删除按钮、把评论组件挂上去。
-->
<script setup>
import { computed, onMounted, ref, watch } from 'vue'
import { useRouter } from 'vue-router'

import { postsApi } from '@/api'
import CommentSection from '@/components/CommentSection.vue'
import MarkdownContent from '@/components/MarkdownContent.vue'
import { useAuthStore } from '@/stores/auth'
import { compactNumber, errorMessage, formatDate, readingTime } from '@/utils/format'

const props = defineProps({
  // 由路由自动注入的文章标识
  slug: { type: String, required: true },
})

const router = useRouter()
const auth = useAuthStore()

const post = ref(null) // 请求成功后才有值，模板靠它判断显示哪种状态
const loading = ref(true)
const error = ref('')

// 能不能管理这篇文章：前端只看"是不是作者本人或管理员"，
// 真正的拦截在后端 permissions.py 里，前端隐藏按钮只是体验优化
const canManage = computed(() => {
  if (!auth.isLoggedIn || !post.value) return false
  return auth.isStaff || auth.user?.id === post.value.author?.id
})

async function load() {
  loading.value = true
  error.value = ''
  post.value = null // 先清空，避免切换文章时短暂看到上一篇的内容
  try {
    post.value = await postsApi.get(props.slug)
  } catch (requestError) {
    // 404 说明文章不存在或是别人的草稿，单独给一句更友好的提示
    error.value =
      requestError.response?.status === 404
        ? '这篇文章不存在，或者已经被作者删除了。'
        : errorMessage(requestError)
  } finally {
    loading.value = false
  }
}

async function remove() {
  if (!window.confirm(`确定删除《${post.value.title}》吗？此操作不可恢复。`)) return
  try {
    await postsApi.remove(post.value.slug)
    // 删掉后回"我的文章"列表
    router.push({ name: 'dashboard' })
  } catch (requestError) {
    error.value = errorMessage(requestError)
  }
}

// 同一个组件在不同文章之间跳转时（slug 变了）要重新请求，
// 否则 Vue 会复用组件、显示的还是上一篇文章
watch(() => props.slug, load)
onMounted(load)
</script>

<template>
  <div class="container container-narrow">
    <!-- 三种状态：加载中 / 出错 / 正文 -->
    <p v-if="loading" class="muted">加载中…</p>
    <p v-else-if="error" class="alert alert-error">{{ error }}</p>

    <article v-else-if="post" class="post-detail">
      <p class="post-detail-topline">
        <RouterLink
          v-if="post.category"
          class="chip chip-category"
          :to="{ name: 'home', query: { category: post.category.slug } }"
        >
          {{ post.category.name }}
        </RouterLink>
        <!-- 草稿只有作者本人看得到，这里再明确提示一次 -->
        <span v-if="post.status === 'draft'" class="chip chip-draft">草稿（仅自己可见）</span>
      </p>

      <h1 class="post-detail-title">{{ post.title }}</h1>

      <div class="post-detail-meta">
        <span>作者 {{ post.author?.username }}</span>
        <span>·</span>
        <span>发布于 {{ formatDate(post.published_at || post.created_at) }}</span>
        <span>·</span>
        <span>{{ readingTime(post.reading_minutes) }}</span>
        <span>·</span>
        <!-- views 由后端在详情接口里自增，所以刷新一次就 +1 -->
        <span>👁 {{ compactNumber(post.views) }} 次阅读</span>
      </div>

      <img v-if="post.cover" class="post-detail-cover" :src="post.cover" :alt="post.title" />

      <!-- 正文是 Markdown 字符串，交给子组件转成 HTML 并做安全过滤 -->
      <MarkdownContent :content="post.body" />

      <div v-if="post.tags?.length" class="post-detail-tags">
        <RouterLink
          v-for="tag in post.tags"
          :key="tag.id"
          class="tag-pill"
          :to="{ name: 'home', query: { tag: tag.slug } }"
        >
          #{{ tag.name }}
        </RouterLink>
      </div>

      <div v-if="canManage" class="post-detail-actions">
        <RouterLink class="btn btn-ghost btn-sm" :to="{ name: 'edit', params: { slug: post.slug } }">
          编辑
        </RouterLink>
        <button class="btn btn-danger btn-sm" type="button" @click="remove">删除</button>
      </div>

      <!-- 评论区自己会去请求数据，这里只要把文章标识传进去 -->
      <CommentSection :slug="post.slug" />
    </article>
  </div>
</template>
