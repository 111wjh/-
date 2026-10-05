<!--
  写作 / 编辑页（一个组件干两件事）。

  • 新建：路由 /write          → props.slug 为空
  • 编辑：路由 /write/<slug>   → props.slug 有值，进页面后先拉取旧内容回填

  提交时有两种格式：不带封面图走 JSON，带了封面图改走 multipart 表单，
  因为文件没法直接塞进 JSON 里。
-->
<script setup>
import { computed, onMounted, reactive, ref } from 'vue'
import { useRouter } from 'vue-router'

import { postsApi, taxonomyApi } from '@/api'
import MarkdownContent from '@/components/MarkdownContent.vue'
import { useAuthStore } from '@/stores/auth'
import { errorMessage } from '@/utils/format'

const props = defineProps({
  // 编辑模式下的文章标识；新建时为空字符串
  slug: { type: String, default: '' },
})

const router = useRouter()
const auth = useAuthStore()

// 有 slug 就是编辑模式，模板里的标题、删除按钮都看这个值
const isEdit = computed(() => Boolean(props.slug))
const tab = ref('write') // 顶部"编写 / 预览"切换
const categories = ref([]) // 分类下拉选项
const coverFile = ref(null) // 用户选中的文件对象，提交时才用
const coverPreview = ref('') // 封面预览地址（本地文件用 URL.createObjectURL 生成）
const loading = ref(false)
const saving = ref(false) // 保存中：禁用所有按钮，顺便防止重复提交
const error = ref('')

// 表单内容。字段名刻意和后端接口对齐，减少来回转换
const form = reactive({
  title: '',
  summary: '',
  body: '',
  categoryId: '',
  status: 'draft',
  isFeatured: false,
  tagText: '',
})

// 输入框里用逗号或空格分隔标签，提交时拆成数组
const tagNames = computed(() =>
  form.tagText
    .split(/[,，\s]+/)
    .map((name) => name.trim())
    .filter(Boolean)
    .slice(0, 8),
)

function onCoverChange(event) {
  const file = event.target.files?.[0]
  if (!file) return
  coverFile.value = file
  // 生成一个临时地址让 <img> 能立刻预览，文件并没有上传
  coverPreview.value = URL.createObjectURL(file)
}

/** 不带文件时用的普通 JSON 载荷 */
function buildJson() {
  return {
    title: form.title,
    summary: form.summary,
    body: form.body,
    status: form.status,
    is_featured: form.isFeatured,
    tag_names: tagNames.value,
    category_id: form.categoryId ? Number(form.categoryId) : null,
  }
}

/**
 * 只在选了封面图时才用 FormData（multipart/form-data）。
 * 注意 DRF 解析表单里的数组要用 tag_names[0]、tag_names[1] 这种写法。
 */
function buildFormData() {
  const data = new FormData()
  data.append('title', form.title)
  data.append('summary', form.summary)
  data.append('body', form.body)
  data.append('status', form.status)
  data.append('is_featured', form.isFeatured ? 'true' : 'false')
  if (form.categoryId) data.append('category_id', String(form.categoryId))
  tagNames.value.forEach((name, index) => data.append(`tag_names[${index}]`, name))
  if (coverFile.value) data.append('cover', coverFile.value)
  return data
}

async function save(status) {
  error.value = ''
  // 必填项在前端先挡一次，省掉一次网络请求（后端仍然会再校验一遍）
  if (!form.title.trim()) {
    error.value = '标题不能为空。'
    return
  }
  if (!form.body.trim()) {
    error.value = '正文不能为空。'
    return
  }

  form.status = status
  saving.value = true
  try {
    // 三选一：带文件用 FormData，编辑走 PATCH，新建走 POST
    const payload = coverFile.value ? buildFormData() : buildJson()
    const saved = isEdit.value
      ? await postsApi.update(props.slug, payload)
      : await postsApi.create(payload)
    // 接口返回的是文章详情，直接拿 slug 跳到成品页看看效果
    router.push({ name: 'post', params: { slug: saved.slug } })
  } catch (requestError) {
    error.value = errorMessage(requestError, '保存失败')
  } finally {
    saving.value = false
  }
}

async function remove() {
  if (!window.confirm('确定删除这篇文章吗？删除后无法恢复。')) return
  try {
    await postsApi.remove(props.slug)
    router.push({ name: 'dashboard' })
  } catch (requestError) {
    error.value = errorMessage(requestError)
  }
}

async function loadPost() {
  loading.value = true
  try {
    const data = await postsApi.get(props.slug)
    // 前端也检查一次归属，避免打开别人的编辑链接后白填一堆字才被后端拒绝
    const mine = auth.user?.id === data.author?.id || auth.isStaff
    if (!mine) {
      error.value = '你没有权限编辑这篇文章。'
      return
    }
    // 把接口数据回填到表单
    form.title = data.title
    form.summary = data.summary
    form.body = data.body
    // <select> 的 v-model 值统一用字符串比较，所以这里把 id 转成字符串
    form.categoryId = data.category?.id ? String(data.category.id) : ''
    form.status = data.status
    form.isFeatured = data.is_featured
    // 标签在多选接口里是数组，编辑时拼成"逗号分隔"的字符串填进输入框
    form.tagText = (data.tags || []).map((tag) => tag.name).join(', ')
    coverPreview.value = data.cover || ''
  } catch (requestError) {
    error.value = errorMessage(requestError)
  } finally {
    loading.value = false
  }
}

onMounted(async () => {
  // 分类下拉先加载；万一失败也不阻塞写文章，用空数组兜底
  const data = await taxonomyApi.categories().catch(() => ({ results: [] }))
  categories.value = data.results
  // 编辑模式才需要回填旧内容
  if (isEdit.value) await loadPost()
})
</script>

<template>
  <div class="container">
    <div class="section-head">
      <h2 class="section-title">{{ isEdit ? '编辑文章' : '写新文章' }}</h2>
      <!-- 编写 / 预览切换：只是切换下面显示哪个块，不涉及接口 -->
      <div class="tabs">
        <button
          class="tab"
          :class="{ active: tab === 'write' }"
          type="button"
          @click="tab = 'write'"
        >
          编写
        </button>
        <button
          class="tab"
          :class="{ active: tab === 'preview' }"
          type="button"
          @click="tab = 'preview'"
        >
          预览
        </button>
      </div>
    </div>

    <p v-if="loading" class="muted">加载中…</p>
    <p v-if="error" class="alert alert-error">{{ error }}</p>

    <div class="editor">
      <!-- 大标题输入框 -->
      <input
        v-model="form.title"
        class="editor-title"
        type="text"
        maxlength="150"
        placeholder="起个标题…"
      />

      <div class="editor-meta">
        <!-- 分类：选项来自后端，值用字符串避免 v-model 类型不一致 -->
        <label class="field field-inline">
          <span>分类</span>
          <select v-model="form.categoryId">
            <option value="">不分类</option>
            <option v-for="item in categories" :key="item.id" :value="String(item.id)">
              {{ item.name }}
            </option>
          </select>
        </label>

        <label class="field field-inline">
          <span>标签</span>
          <input v-model="form.tagText" type="text" placeholder="用逗号分隔，例如：Django, 踩坑" />
        </label>

        <label class="field field-inline field-checkbox">
          <input v-model="form.isFeatured" type="checkbox" />
          <span>置顶推荐</span>
        </label>
      </div>

      <label class="field">
        <span>摘要（留空会自动从正文生成）</span>
        <!-- 摘要留空时后端会从正文里截一段，见 blog/models.py 的 build_summary() -->
        <textarea v-model="form.summary" rows="2" maxlength="300"></textarea>
      </label>

      <!-- 两个页签互斥：tab 是 write 显示文本域，否则显示渲染结果 -->
      <template v-if="tab === 'write'">
        <label class="field">
          <span>正文（支持 Markdown）</span>
          <textarea
            v-model="form.body"
            class="editor-body"
            rows="18"
            placeholder="# 标题&#10;&#10;正文支持 **加粗**、`代码`、代码块：&#10;&#10;```python&#10;print('hello')&#10;```"
          ></textarea>
        </label>
      </template>
      <div v-else class="editor-preview">
        <!-- 预览复用了详情页同款的 Markdown 组件，所见即所得 -->
        <h3 v-if="form.title" class="post-detail-title">{{ form.title }}</h3>
        <MarkdownContent :content="form.body || '*（还没有内容）*'" />
      </div>

      <label class="field">
        <span>封面图（可选）</span>
        <!-- change 事件里拿文件对象，文件本身不在这里上传 -->
        <input type="file" accept="image/*" @change="onCoverChange" />
      </label>
      <img v-if="coverPreview" class="editor-cover-preview" :src="coverPreview" alt="封面预览" />

      <div class="editor-actions">
        <!-- 同一个 save() 函数，传不同状态就是"存草稿"或"发布" -->
        <button class="btn btn-ghost" type="button" :disabled="saving" @click="save('draft')">
          保存草稿
        </button>
        <button class="btn btn-primary" type="button" :disabled="saving" @click="save('published')">
          {{ saving ? '保存中…' : '发布文章' }}
        </button>
        <span class="spacer"></span>
        <button
          v-if="isEdit"
          class="btn btn-danger"
          type="button"
          :disabled="saving"
          @click="remove"
        >
          删除
        </button>
        <RouterLink class="btn btn-ghost" :to="{ name: 'dashboard' }">取消</RouterLink>
      </div>
    </div>
  </div>
</template>
