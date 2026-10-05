<!--
  文章底部的评论区：列表 + 发表框 + 删除。

  这里演示了几个常见做法：
    * 接口地址由父组件传进来（props.slug），组件不写死文章
    * 未登录只显示"去登录"，但有权限校验的始终是后端
    * 发表成功后不重新请求整个列表，而是直接把新评论插到最前面
-->
<script setup>
import { onMounted, ref } from 'vue'

import { commentsApi, postsApi } from '@/api'
import { useAuthStore } from '@/stores/auth'
import { errorMessage, relativeTime } from '@/utils/format'

const props = defineProps({
  // 文章的唯一标识，用来拼接口地址 /posts/<slug>/comments/
  slug: { type: String, required: true },
})

const auth = useAuthStore()
const comments = ref([]) // 评论列表
const total = ref(0) // 评论总数，单独存是因为接口返回的 count 才是权威值
const loading = ref(false) // 首次加载中
const submitting = ref(false) // 正在发表，用来禁用按钮防连点
const draft = ref('') // 输入框里的内容
const feedback = ref('') // 错误提示文字

/** 拉取评论列表。父组件挂载这个组件时调用一次 */
async function load() {
  loading.value = true
  try {
    // page_size=50：小博客评论不多，一次拿完，省掉翻页逻辑
    const data = await postsApi.comments(props.slug, { page_size: 50 })
    comments.value = data.results
    total.value = data.count
  } catch (error) {
    // 后端返回的错误结构五花八门，统一交给 errorMessage() 翻译成人话
    feedback.value = errorMessage(error)
  } finally {
    // 不管成功失败都要把 loading 关掉，否则页面会一直转圈
    loading.value = false
  }
}

/** 发表评论 */
async function submit() {
  if (!draft.value.trim()) return // 空内容直接忽略
  submitting.value = true
  feedback.value = ''
  try {
    const created = await postsApi.addComment(props.slug, draft.value.trim())
    // 后端按"新评论在前"排序，所以这里也插到数组最前面，顺序才一致
    comments.value = [created, ...comments.value]
    total.value += 1
    draft.value = '' // 清空输入框
  } catch (error) {
    feedback.value = errorMessage(error, '评论发表失败')
  } finally {
    submitting.value = false
  }
}

/** 删除自己的评论 */
async function remove(comment) {
  // window.confirm 是最省事的二次确认；正式项目一般换成自定义弹窗
  if (!window.confirm('确定删除这条评论吗？')) return
  try {
    await commentsApi.remove(comment.id)
    // 删除成功后从本地数组里过滤掉，不用重新请求列表
    comments.value = comments.value.filter((item) => item.id !== comment.id)
    total.value -= 1
  } catch (error) {
    feedback.value = errorMessage(error)
  }
}

// 组件挂载后自动加载评论
onMounted(load)
</script>

<template>
  <section class="comment-section">
    <h3 class="section-title">评论 <span class="count">{{ total }}</span></h3>

    <!-- 登录了才给输入框，没登录就提示去登录 -->
    <form v-if="auth.isLoggedIn" class="comment-form" @submit.prevent="submit">
      <textarea
        v-model="draft"
        rows="3"
        maxlength="500"
        placeholder="说点什么吧…（最多 500 字）"
      ></textarea>
      <div class="comment-form-actions">
        <!-- 实时字数统计，和后端 500 字的上限保持一致 -->
        <span class="hint">{{ draft.length }} / 500</span>
        <button class="btn btn-primary btn-sm" type="submit" :disabled="submitting">
          {{ submitting ? '发表中…' : '发表评论' }}
        </button>
      </div>
    </form>

    <p v-else class="comment-login-hint">
      登录后即可参与评论。
      <RouterLink :to="{ name: 'login' }">去登录</RouterLink>
    </p>

    <p v-if="feedback" class="alert alert-error">{{ feedback }}</p>

    <p v-if="loading" class="muted">评论加载中…</p>
    <p v-else-if="!comments.length" class="muted">还没有评论，来做第一个吧。</p>

    <ul class="comment-list">
      <li v-for="item in comments" :key="item.id" class="comment-item">
        <!-- 没有头像图片，就用用户名的首字母做圆形占位 -->
        <div class="comment-avatar">{{ item.author?.username?.slice(0, 1) || '?' }}</div>
        <div class="comment-main">
          <div class="comment-head">
            <strong>{{ item.author?.username || '已注销用户' }}</strong>
            <span class="muted">{{ relativeTime(item.created_at) }}</span>
            <!-- is_owner 由后端算好：只有自己的评论才显示删除按钮 -->
            <button
              v-if="item.is_owner"
              class="link-danger"
              type="button"
              @click="remove(item)"
            >
              删除
            </button>
          </div>
          <p class="comment-content">{{ item.content }}</p>
        </div>
      </li>
    </ul>
  </section>
</template>
