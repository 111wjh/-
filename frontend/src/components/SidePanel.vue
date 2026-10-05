<!--
  首页右侧栏：搜索框 + 分类 + 标签 + 归档。

  设计要点：这个组件**只负责展示和跳转，不自己发请求**。
  分类/标签/归档的数据由 HomeView 请求好后通过 props 传进来，
  搜索则是抛一个 search 事件出去，让 HomeView 去改网址参数。
  这样数据来源只有一处，调试时不用满项目找"这个列表是谁请求的"。
-->
<script setup>
import { ref } from 'vue'

// default: () => [] 是数组默认值的固定写法（直接写 [] 会让所有实例共用同一个数组）
const props = defineProps({
  categories: { type: Array, default: () => [] },
  tags: { type: Array, default: () => [] },
  archive: { type: Array, default: () => [] },
  activeCategory: { type: String, default: '' },
  activeTag: { type: String, default: '' },
  keyword: { type: String, default: '' },
})

const emit = defineEmits(['search'])
// 输入框用本地状态，避免用户每敲一个字就触发一次搜索；
// 初始值取当前网址上的关键词，这样刷新页面后搜索框里还留着上次搜的词
const draft = ref(props.keyword)

function submit() {
  // 去掉首尾空格再抛给父组件；trim 后为空表示"清空搜索"
  emit('search', draft.value.trim())
}
</script>

<template>
  <aside class="side-panel">
    <!-- 搜索：@submit.prevent 阻止表单默认的整页刷新，交给 JS 处理 -->
    <section class="panel">
      <h4 class="panel-title">搜索</h4>
      <form class="search-form" @submit.prevent="submit">
        <input v-model="draft" type="search" placeholder="标题、摘要或正文…" />
        <button class="btn btn-primary btn-sm" type="submit">搜索</button>
      </form>
    </section>

    <!-- 分类：点任何一个都只是切换网址上的 ?category=xxx，页面不刷新 -->
    <section class="panel">
      <h4 class="panel-title">分类</h4>
      <ul class="panel-list">
        <li>
          <!-- 没有 category 参数时，"全部文章"这一项算选中状态 -->
          <RouterLink :to="{ name: 'home' }" :class="{ active: !activeCategory }">
            全部文章
          </RouterLink>
        </li>
        <li v-for="item in categories" :key="item.id">
          <RouterLink
            :to="{ name: 'home', query: { category: item.slug } }"
            :class="{ active: activeCategory === item.slug }"
          >
            {{ item.name }}
            <!-- post_count 是后端 annotate 算好的文章数，前端不再单独请求 -->
            <span class="count">{{ item.post_count }}</span>
          </RouterLink>
        </li>
      </ul>
    </section>

    <section class="panel">
      <h4 class="panel-title">标签</h4>
      <div class="tag-cloud">
        <RouterLink
          v-for="item in tags"
          :key="item.id"
          class="tag-pill"
          :class="{ active: activeTag === item.slug }"
          :to="{ name: 'home', query: { tag: item.slug } }"
        >
          #{{ item.name }}<span class="count">{{ item.post_count }}</span>
        </RouterLink>
      </div>
    </section>

    <section class="panel">
      <h4 class="panel-title">归档</h4>
      <ul class="panel-list">
        <li v-for="item in archive" :key="`${item.year}-${item.month}`">
          <RouterLink
            :to="{ name: 'home', query: { year: item.year, month: item.month } }"
          >
            {{ item.year }} 年 {{ item.month }} 月
            <span class="count">{{ item.count }}</span>
          </RouterLink>
        </li>
      </ul>
    </section>
  </aside>
</template>
