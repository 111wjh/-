<!--
  文章卡片：首页列表里的一个条目。
  这是典型的"展示型组件" —— 自己不请求数据，只负责把父组件传进来的 post 对象画出来。
-->
<script setup>
import { computed } from 'vue'

import { compactNumber, formatDate, readingTime } from '@/utils/format'

// defineProps 声明父组件能传什么进来：post 是必填的对象
const props = defineProps({
  post: { type: Object, required: true },
})

// 卡片标题、配图都指向文章详情页；用计算属性避免在模板里重复拼参数
const to = computed(() => ({ name: 'post', params: { slug: props.post.slug } }))
// 没有封面图时，用标题第一个字做占位方块
const initial = computed(() => props.post.title?.slice(0, 1) || '文')
</script>

<template>
  <article class="post-card">
    <!-- 整块封面可点击；? 是可选链，post.author 不存在时不会报错，只是渲染成空 -->
    <RouterLink class="post-card-cover" :to="to">
      <img v-if="post.cover" :src="post.cover" :alt="post.title" loading="lazy" />
      <span v-else class="cover-placeholder">{{ initial }}</span>
    </RouterLink>

    <div class="post-card-body">
      <div class="post-card-topline">
        <!-- 分类、置顶、草稿三种角标。分类链接直接跳到"按分类筛选"的首页 -->
        <RouterLink
          v-if="post.category"
          class="chip chip-category"
          :to="{ name: 'home', query: { category: post.category.slug } }"
        >
          {{ post.category.name }}
        </RouterLink>
        <span v-if="post.is_featured" class="chip chip-featured">置顶</span>
        <span v-if="post.status === 'draft'" class="chip chip-draft">草稿</span>
      </div>

      <h3 class="post-card-title">
        <RouterLink :to="to">{{ post.title }}</RouterLink>
      </h3>

      <!-- 摘要是后端从 Markdown 正文里自动截出来的纯文本 -->
      <p class="post-card-summary">{{ post.summary }}</p>

      <div class="post-card-meta">
        <span>{{ post.author?.username }}</span>
        <span>·</span>
        <!-- 已发布的用发布时间，草稿只有创建时间 -->
        <span>{{ formatDate(post.published_at || post.created_at) }}</span>
        <span>·</span>
        <span>{{ readingTime(post.reading_minutes) }}</span>
        <span>·</span>
        <span>👁 {{ compactNumber(post.views) }}</span>
        <span>·</span>
        <span>💬 {{ post.comment_count }}</span>
      </div>

      <!-- v-for 一定要给 :key，Vue 靠它判断哪个节点被增删，避免复用错节点 -->
      <div v-if="post.tags?.length" class="post-card-tags">
        <RouterLink
          v-for="tag in post.tags"
          :key="tag.id"
          class="tag-pill"
          :to="{ name: 'home', query: { tag: tag.slug } }"
        >
          #{{ tag.name }}
        </RouterLink>
      </div>
    </div>
  </article>
</template>
