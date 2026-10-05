<!--
  把 Markdown 正文渲染成 HTML 的组件。

  流程一共三步：
    1. marked       Markdown 源码 → HTML 字符串
    2. DOMPurify    过滤掉 <script> 之类的危险标签（防 XSS）
    3. highlight.js 给代码块上色
  只要有一步偷懒，要么格式显示不出来，要么就是一个 XSS 漏洞。
-->
<script setup>
import DOMPurify from 'dompurify'
// 只引入 hljs 内核 + 需要的语言包。
// 直接 import 'highlight.js' 会把 190 多种语言全打进包里（约 1MB），这里只留常用的几种。
import hljs from 'highlight.js/lib/core'
import bash from 'highlight.js/lib/languages/bash'
import css from 'highlight.js/lib/languages/css'
import javascript from 'highlight.js/lib/languages/javascript'
import json from 'highlight.js/lib/languages/json'
import python from 'highlight.js/lib/languages/python'
import sql from 'highlight.js/lib/languages/sql'
import xml from 'highlight.js/lib/languages/xml'
import { marked } from 'marked'
import { computed, nextTick, onMounted, ref, watch } from 'vue'

hljs.registerLanguage('bash', bash)
hljs.registerLanguage('css', css)
hljs.registerLanguage('javascript', javascript)
hljs.registerLanguage('json', json)
hljs.registerLanguage('python', python)
hljs.registerLanguage('sql', sql)
hljs.registerLanguage('xml', xml)
hljs.registerLanguage('html', xml)

const props = defineProps({
  // 父组件传进来的 Markdown 源码
  content: { type: String, default: '' },
})

// 模板 ref：用来在渲染完成后拿到这个 div 的真实 DOM 节点，好去操作里面的代码块
const container = ref(null)

// gfm 打开 GitHub 风格的表格、任务列表；breaks=false 表示单个换行不当成新段落
marked.setOptions({ gfm: true, breaks: false })

// 两步走：marked 把 Markdown 变成 HTML，DOMPurify 再把危险标签（<script> 等）洗掉。
// 正文是作者自己写的，但只要渲染 HTML，这一步就不能省。
const html = computed(() =>
  DOMPurify.sanitize(marked.parse(props.content || ''), { ADD_ATTR: ['target'] }),
)

// 代码高亮要在 DOM 渲染出来之后做
async function highlight() {
  // nextTick 等 Vue 把最新的 HTML 真正写进页面，否则查不到 <pre><code>
  await nextTick()
  container.value?.querySelectorAll('pre code').forEach((block) => {
    // dataset 标记防止重复高亮（同一个节点被处理两次会把颜色套两层）
    if (!block.dataset.highlighted) {
      hljs.highlightElement(block)
      block.dataset.highlighted = 'yes'
    }
  })
}

// 正文变了要重新高亮；首次挂载时也要执行一次
watch(html, highlight)
onMounted(highlight)
</script>

<template>
  <!-- ref="container" 把上面声明的 ref 绑到这个 div 上 -->
  <!-- v-html 是"把字符串当 HTML 插入"的指令，这里是整个项目唯一该用它的地方，
       前提是内容已经过了 DOMPurify -->
  <div ref="container" class="markdown-body" v-html="html"></div>
</template>
