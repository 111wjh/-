<!--
  归档页：按年份分组，列出每个月的文章数。
  后端 /api/archive/ 返回的是扁平的 [{year, month, count}, ...]，
  这里用计算属性把它整理成"按年分组"的结构再渲染。
-->
<script setup>
import { computed, onMounted, ref } from 'vue'

import { taxonomyApi } from '@/api'
import { errorMessage } from '@/utils/format'

const rows = ref([]) // 接口原始数据
const loading = ref(true)
const error = ref('')

// 后端给的是扁平的 [{year, month, count}]，这里按年份分组，方便分栏展示
const groups = computed(() => {
  const map = new Map()
  rows.value.forEach((item) => {
    if (!map.has(item.year)) map.set(item.year, [])
    map.get(item.year).push(item)
  })
  return Array.from(map, ([year, items]) => ({ year, items }))
})

const totalPosts = computed(() => rows.value.reduce((sum, item) => sum + item.count, 0))

// 页面一进来就请求归档数据
onMounted(async () => {
  try {
    rows.value = await taxonomyApi.archive()
  } catch (requestError) {
    error.value = errorMessage(requestError)
  } finally {
    loading.value = false
  }
})
</script>

<template>
  <div class="container container-narrow">
    <div class="section-head">
      <h2 class="section-title">归档</h2>
      <span class="muted">共 {{ totalPosts }} 篇</span>
    </div>

    <p v-if="error" class="alert alert-error">{{ error }}</p>
    <p v-else-if="loading" class="muted">加载中…</p>
    <p v-else-if="!groups.length" class="empty-state">还没有已发布的文章。</p>

    <section v-for="group in groups" :key="group.year" class="archive-group">
      <h3 class="archive-year">{{ group.year }} 年</h3>
      <ul class="archive-list">
        <!-- 点某个月 → 跳到首页并带上 ?year=&month=，由首页去请求那个月的文章 -->
        <li v-for="item in group.items" :key="`${item.year}-${item.month}`">
          <RouterLink :to="{ name: 'home', query: { year: item.year, month: item.month } }">
            {{ item.month }} 月
          </RouterLink>
          <span class="muted">{{ item.count }} 篇</span>
        </li>
      </ul>
    </section>
  </div>
</template>
