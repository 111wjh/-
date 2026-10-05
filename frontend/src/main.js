/**
 * 前端入口文件。
 *
 * Vite 从 index.html 里的 <script type="module" src="/src/main.js"> 开始执行，
 * 所以整个单页应用就是在这里被创建、装上插件，然后挂到页面上的 <div id="app">。
 */
import { createApp } from 'vue'
import { createPinia } from 'pinia'

// 代码高亮主题的样式（highlight.js 自带），必须在自己的样式之前引入，
// 这样后面写的 main.css 才有机会覆盖它的默认字体和行高
import 'highlight.js/styles/github.css'
import '@/assets/main.css'

import App from '@/App.vue'
import router from '@/router'

// createApp(根组件)：创建应用实例，之后所有组件都挂在这棵树下
const app = createApp(App)

// Pinia 管全局状态（比如"当前登录用户"），router 管页面切换
app.use(createPinia())
app.use(router)

// 把应用渲染到 index.html 里 id="app" 的那个 div 上
app.mount('#app')
