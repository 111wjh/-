<!--
  首页：置顶推荐 + 文章列表 + 右侧栏。

  这个页面的核心思路是 —— **筛选状态全部存在网址上**。
  分类、标签、关键词、年月、翻页都读自 route.query，
  用户点筛选等于改网址，watch 监听到网址变化再重新请求接口。
  好处：刷新不丢筛选、链接可以直接分享、浏览器前进后退也正常工作。
-->
<script setup>
import { computed, onMounted, ref, watch } from 'vue'
import { useRoute, useRouter } from 'vue-router'

import { postsApi, taxonomyApi } from '@/api'
import PagerBar from '@/components/PagerBar.vue'
import PostCard from '@/components/PostCard.vue'
import SidePanel from '@/components/SidePanel.vue'
import { errorMessage, formatDate, readingTime } from '@/utils/format'

const route = useRoute()
const router = useRouter()

// 每页条数。改这里就能调整一页显示几篇文章
const PAGE_SIZE = 6

const posts = ref([]) // 当前页的文章
const featured = ref([]) // 置顶推荐，用来做首屏大卡片
const total = ref(0) // 符合条件的文章总数（后端返回的 count）
const page = ref(1) // 当前页码（只存在内存里，不放网址，避免和筛选条件互相干扰）
const loading = ref(false)
const error = ref('')

// 右侧栏数据
const categories = ref([])
const tags = ref([])
const archive = ref([])

// 这些筛选条件都放在网址上（?category=django&tag=vue），刷新和分享都不会丢
const activeCategory = computed(() => String(route.query.category || ''))
const activeTag = computed(() => String(route.query.tag || ''))
const keyword = computed(() => String(route.query.search || ''))
const activeYear = computed(() => String(route.query.year || ''))
const activeMonth = computed(() => String(route.query.month || ''))

const hasFilter = computed(() =>
  Boolean(activeCategory.value || activeTag.value || keyword.value || activeYear.value),
)
const totalPages = computed(() => Math.max(1, Math.ceil(total.value / PAGE_SIZE)))
// 只在"没有任何筛选"且在第一页时才显示置顶卡片
const showFeatured = computed(() => !hasFilter.value && page.value === 1 && featured.value.length > 0)

// 列表上方那行标题，随筛选条件变化：搜索「xx」/ 标签 #xx / 分类：xx / 2026 年 9 月
const heading = computed(() => {
  if (keyword.value) return `搜索「${keyword.value}」`
  if (activeTag.value) {
    const tag = tags.value.find((item) => item.slug === activeTag.value)
    return `标签 #${tag?.name || activeTag.value}`
  }
  if (activeCategory.value) {
    const category = categories.value.find((item) => item.slug === activeCategory.value)
    return `分类：${category?.name || activeCategory.value}`
  }
  if (activeYear.value) {
    return activeMonth.value
      ? `${activeYear.value} 年 ${Number(activeMonth.value)} 月`
      : `${activeYear.value} 年`
  }
  return '最新文章'
})

async function loadPosts() {
  loading.value = true
  error.value = ''
  try {
    // 只把有值的条件放进参数，避免给后端发一堆空字符串
    const params = { page: page.value, page_size: PAGE_SIZE }
    if (activeCategory.value) params.category = activeCategory.value
    if (activeTag.value) params.tag = activeTag.value
    if (keyword.value) params.search = keyword.value
    if (activeYear.value) params.year = activeYear.value
    if (activeMonth.value) params.month = activeMonth.value

    // 后端返回 { count, next, previous, results } 的标准分页结构
    const data = await postsApi.list(params)
    posts.value = data.results
    total.value = data.count
  } catch (requestError) {
    error.value = errorMessage(requestError)
  } finally {
    loading.value = false
  }
}

/** 右侧栏的三个接口互不依赖，用 Promise.all 并行发，比一个一个 await 快 */
async function loadSidebar() {
  try {
    const [categoryData, tagData, archiveData] = await Promise.all([
      taxonomyApi.categories(),
      taxonomyApi.tags(),
      taxonomyApi.archive(),
    ])
    categories.value = categoryData.results
    tags.value = tagData.results
    archive.value = archiveData
  } catch (requestError) {
    // 侧边栏失败不影响正文，静默处理即可
    console.warn('[sidebar]', errorMessage(requestError))
  }
}

async function loadFeatured() {
  try {
    featured.value = await postsApi.featured()
  } catch {
    // 置顶只是锦上添花，失败了就当没有，不要影响主列表
    featured.value = []
  }
}

/** 翻页：换页码 → 重新请求 → 滚回顶部 */
function changePage(target) {
  page.value = target
  loadPosts()
  window.scrollTo({ top: 0, behavior: 'smooth' })
}

/** 搜索：改网址参数，真正的请求由下面的 watch 触发 */
function search(value) {
  router.push({ name: 'home', query: value ? { search: value } : {} })
}

// 筛选条件一变就回到第一页重新请求
watch(
  () => [activeCategory.value, activeTag.value, keyword.value, activeYear.value, activeMonth.value],
  () => {
    page.value = 1
    loadPosts()
  },
)

onMounted(() => {
  // 首次进入页面：三件事并行做，互不阻塞
  loadSidebar()
  loadFeatured()
  loadPosts()
})
</script>

<template>
  <div class="container page-grid">
    <div class="page-main">
      <!-- 置顶推荐：只有首页、第一页、没有筛选时才出现 -->
      <section v-if="showFeatured" class="hero">
        <p class="hero-label">置顶推荐</p>
        <h1 class="hero-title">
          <RouterLink :to="{ name: 'post', params: { slug: featured[0].slug } }">
            {{ featured[0].title }}
          </RouterLink>
        </h1>
        <p class="hero-summary">{{ featured[0].summary }}</p>
        <p class="hero-meta">
          <span>{{ featured[0].author?.username }}</span>
          <span>·</span>
          <span>{{ formatDate(featured[0].published_at || featured[0].created_at) }}</span>
          <span>·</span>
          <span>{{ readingTime(featured[0].reading_minutes) }}</span>
        </p>
      </section>

      <div class="section-head">
        <h2 class="section-title">{{ heading }}</h2>
        <span class="muted">共 {{ total }} 篇</span>
      </div>

      <!-- 三种状态互斥：报错 → 加载中 → 内容/空 -->
      <p v-if="error" class="alert alert-error">{{ error }}</p>
      <p v-if="loading" class="muted">加载中…</p>

      <template v-else>
        <p v-if="!posts.length" class="empty-state">
          这里还没有文章。换个筛选条件，或者去
          <RouterLink :to="{ name: 'write' }">写一篇</RouterLink>。
        </p>
        <div v-else class="post-list">
          <!-- 列表渲染：PostCard 是子组件，post 通过 props 传进去 -->
          <PostCard v-for="item in posts" :key="item.id" :post="item" />
        </div>
        <!-- 子组件点页码时抛 change 事件，这里接到后调用 changePage -->
        <PagerBar :page="page" :total-pages="totalPages" @change="changePage" />
      </template>
    </div>

    <!-- 右侧栏：数据靠 props 传入，搜索靠监听 search 事件 -->
    <SidePanel
      :categories="categories"
      :tags="tags"
      :archive="archive"
      :active-category="activeCategory"
      :active-tag="activeTag"
      :keyword="keyword"
      @search="search"
    />
  </div>
</template>
