<!--
  分页条。这里演示了 Vue 组件之间最标准的两种通信方式：
    props  向下传数据（当前页、总页数）
    emits  向上抛事件（用户点了第几页）
  组件本身不关心数据从哪来，父组件接到 @change 后自己去请求接口。
-->
<script setup>
import { computed } from 'vue'

const props = defineProps({
  page: { type: Number, default: 1 },
  totalPages: { type: Number, default: 1 },
})

// 声明本组件会向父组件抛出的事件名，父组件用 @change="处理函数" 接收
const emit = defineEmits(['change'])

// 只显示当前页附近的页码，避免页数很多时把导航撑爆
const pages = computed(() => {
  const total = props.totalPages
  const current = props.page
  const list = []
  // 先算出窗口的左右边界，再保证边界不越出 1..total 的范围
  const start = Math.max(1, Math.min(current - 2, total - 4))
  const end = Math.min(total, Math.max(current + 2, 5))
  for (let index = start; index <= end; index += 1) list.push(index)
  return list
})

function go(target) {
  // 越界或者点的就是当前页，什么都不做
  if (target < 1 || target > props.totalPages || target === props.page) return
  emit('change', target)
}
</script>

<template>
  <!-- 只有一页时不显示分页条 -->
  <nav v-if="totalPages > 1" class="pager">
    <button class="btn btn-ghost btn-sm" type="button" :disabled="page <= 1" @click="go(page - 1)">
      上一页
    </button>
    <!-- :class 也可以用对象语法：active 这个类只在"是当前页"时才加上去 -->
    <button
      v-for="item in pages"
      :key="item"
      class="pager-num"
      :class="{ active: item === page }"
      type="button"
      @click="go(item)"
    >
      {{ item }}
    </button>
    <button
      class="btn btn-ghost btn-sm"
      type="button"
      :disabled="page >= totalPages"
      @click="go(page + 1)"
    >
      下一页
    </button>
  </nav>
</template>
