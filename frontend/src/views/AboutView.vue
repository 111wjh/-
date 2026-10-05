<!--
  关于页：纯静态内容，没有任何接口调用。
  这种页面直接写死在 .vue 里最省事；只有需要被搜索收录或频繁改动时，
  才值得做成后端配置或 Markdown 文件。
-->
<template>
  <div class="container container-narrow">
    <h1 class="section-title">关于这个项目</h1>
    <p class="muted">一个用来学习 Django 的个人博客，前后端完全分离。</p>

    <section class="panel">
      <h4 class="panel-title">技术栈</h4>
      <ul class="plain-list">
        <li><strong>后端</strong>：Django 6.1 + Django REST Framework，SQLite 存数据，JWT 做登录</li>
        <li><strong>前端</strong>：Vue 3 + Vite + Vue Router + Pinia + axios</li>
        <li><strong>写作</strong>：Django Admin（<code>/admin/</code>）或前端的写文章页面</li>
      </ul>
    </section>

    <section class="panel">
      <h4 class="panel-title">前后端怎么配合</h4>
      <ol class="plain-list">
        <li>前端页面加载后，用 axios 请求 <code>http://127.0.0.1:8000/api/...</code></li>
        <li>后端从数据库取数据，用序列化器转成 JSON 返回</li>
        <li>登录后前端拿到 JWT，之后每个请求都带 <code>Authorization: Bearer …</code></li>
        <li>access 过期时，前端自动用 refresh 换新的 token 并重发请求</li>
      </ol>
    </section>

    <section class="panel">
      <h4 class="panel-title">主要接口</h4>
      <table class="api-table">
        <thead>
          <tr>
            <th>方法</th>
            <th>地址</th>
            <th>说明</th>
          </tr>
        </thead>
        <tbody>
          <tr><td>GET</td><td>/api/posts/</td><td>文章列表（分页、筛选、搜索）</td></tr>
          <tr><td>GET</td><td>/api/posts/&lt;slug&gt;/</td><td>文章详情，阅读量 +1</td></tr>
          <tr><td>POST</td><td>/api/posts/</td><td>新建文章（需登录）</td></tr>
          <tr><td>GET</td><td>/api/posts/&lt;slug&gt;/comments/</td><td>评论列表</td></tr>
          <tr><td>POST</td><td>/api/auth/login/</td><td>登录，返回 access / refresh</td></tr>
          <tr><td>POST</td><td>/api/auth/register/</td><td>注册</td></tr>
          <tr><td>GET</td><td>/api/auth/me/</td><td>当前登录用户</td></tr>
          <tr><td>GET</td><td>/api/categories/</td><td>分类及各自的文章数</td></tr>
          <tr><td>GET</td><td>/api/tags/</td><td>标签</td></tr>
          <tr><td>GET</td><td>/api/archive/</td><td>按月份统计文章数</td></tr>
        </tbody>
      </table>
      <p class="muted">
        完整的接口目录、以及能直接点着调试的网页版界面在
        <a href="http://127.0.0.1:8000/api/" target="_blank" rel="noreferrer">/api/</a>。
      </p>
    </section>

    <section class="panel">
      <h4 class="panel-title">演示账号</h4>
      <ul class="plain-list">
        <li>普通用户：<code>demo / demo12345</code>（也是现有文章的作者）</li>
        <li>普通用户：<code>reader / reader12345</code></li>
        <li>管理员：<code>admin / admin123456</code>，可登录 <code>/admin/</code> 写作后台</li>
      </ul>
      <p class="muted">这些都是本地学习用的假数据，正式部署前请务必改掉。</p>
    </section>
  </div>
</template>
