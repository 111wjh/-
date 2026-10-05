<!--
  页脚。除了版权文字，还提供两个"后端专属"的入口：
  DRF 的接口目录页和 Django Admin 写作后台，方便开发时直接点过去。
-->
<script setup>
import { API_BASE_URL } from '@/api/http'

// API_BASE_URL 可能是完整的 http://... （开发环境），也可能是 /api 这样的相对路径（生产环境）。
// 相对路径直接写进 <a href> 会跑到当前站点，所以这里补上当前域名。
const backendUrl = API_BASE_URL.startsWith('http')
  ? API_BASE_URL
  : `${window.location.origin}${API_BASE_URL}`
</script>

<template>
  <footer class="site-footer">
    <div class="container footer-inner">
      <p>学习日志 · 用 Django REST Framework + Vue 3 搭的前后端分离博客</p>
      <p class="footer-links">
        <!-- 新窗口打开要加 rel="noreferrer"，防止被打开的页面通过 window.opener 操作当前页 -->
        <a :href="backendUrl" target="_blank" rel="noreferrer">接口目录 (/api/)</a>
        <a href="http://127.0.0.1:8000/admin/" target="_blank" rel="noreferrer">写作后台 (/admin/)</a>
      </p>
    </div>
  </footer>
</template>
