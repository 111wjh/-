<!-- 404 页：路由表最后的通配规则会把所有匹配不上的地址指到这里 -->
<template>
  <div class="container container-narrow not-found">
    <h1>404</h1>
    <p class="muted">这个页面不存在，可能是链接写错了。</p>
    <RouterLink class="btn btn-primary" :to="{ name: 'home' }">回到首页</RouterLink>
  </div>
</template>
