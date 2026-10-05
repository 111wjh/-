# 学习日志 · Django + Vue 前后端分离博客

一个用来练习 Django 的小型个人博客。**后端只输出 JSON，前端只负责界面**，两边通过 HTTP 接口通信，可以独立开发、独立部署。

## 技术栈

| 部分 | 技术 |
| --- | --- |
| 后端 | Django 6.1、Django REST Framework 3.18、Simple JWT、django-cors-headers、SQLite |
| 前端 | Vue 3、Vite、Vue Router、Pinia、axios、marked、highlight.js、DOMPurify |
| 写作后台 | Django Admin（`/admin/`），或前端自带的写文章页面 |

## 目录结构

```
Learning Log/
├─ Learning_Log/           # 项目配置：settings.py（含 CORS、JWT、DRF 配置）、urls.py
├─ blog/                   # 唯一的应用，整个后端业务都在这里
│  ├─ models.py            # 数据模型：分类、标签、文章、评论
│  ├─ serializers.py       # 序列化器：模型 ←→ JSON
│  ├─ views.py             # 视图（ViewSet）：对外提供哪些接口
│  ├─ permissions.py       # 权限：谁能改什么
│  ├─ pagination.py        # 分页配置
│  ├─ urls.py              # 路由（DefaultRouter 自动生成）
│  ├─ admin.py             # 写作后台的配置
│  └─ management/commands/seed_blog.py   # 生成演示数据
├─ frontend/               # Vue 3 单页应用（完全独立于 Django）
│  ├─ src/api/             # axios 实例、拦截器、接口清单
│  ├─ src/stores/          # Pinia：登录状态
│  ├─ src/router/          # 前端路由 + 登录守卫
│  ├─ src/views/           # 页面：首页、详情、归档、登录、写作、我的文章…
│  └─ src/components/      # 组件：文章卡片、侧边栏、评论、Markdown 渲染…
├─ requirements.txt
└─ db.sqlite3              # 数据库（已被 .gitignore 忽略）
```

## 快速开始

需要 Python 3.10+ 和 Node.js 18+。

### 1. 启动后端（Django）

```powershell
# 在项目根目录
.\.venv\Scripts\Activate.ps1          # 激活虚拟环境（首次可跳过，直接用下面的完整路径）
pip install -r requirements.txt

python manage.py migrate              # 建表
python manage.py seed_blog --admin    # 生成演示数据 + 管理员账号
python manage.py runserver            # 启动，默认 http://127.0.0.1:8000
```

启动后可以打开 <http://127.0.0.1:8000/api/> 看到 DRF 自动生成的接口目录页，
在那里可以直接点着调试每个接口，写前端之前先用它把接口验一遍。

### 2. 启动前端（Vue）

```powershell
cd frontend
npm install
npm run dev        # http://localhost:5173
```

浏览器打开 <http://localhost:5173> 就能看到博客首页。

### 演示账号

| 账号 | 密码 | 说明 |
| --- | --- | --- |
| `demo` | `demo12345` | 普通用户，现有文章都是他写的；登录页有「一键填入」 |
| `reader` | `reader12345` | 普通用户，用来测试「别人的文章不能改」 |
| `admin` | `admin123456` | 管理员，可登录 `/admin/` 写作后台 |

> 这些都是本地学习用的假账号，正式部署前记得改掉 `SECRET_KEY` 并删掉它们。

## 接口一览

| 方法 | 地址 | 说明 | 是否需要登录 |
| --- | --- | --- | --- |
| GET | `/api/posts/` | 文章列表（分页 / 筛选 / 搜索 / 排序） | 否 |
| POST | `/api/posts/` | 新建文章 | 是 |
| GET | `/api/posts/<slug>/` | 文章详情，阅读量 +1 | 否 |
| PATCH / DELETE | `/api/posts/<slug>/` | 修改 / 删除文章 | 仅作者或管理员 |
| GET / POST | `/api/posts/<slug>/comments/` | 评论列表 / 发表评论 | 发表需登录 |
| DELETE | `/api/comments/<id>/` | 删除评论 | 仅评论者或管理员 |
| GET | `/api/posts/featured/` | 首页置顶推荐 | 否 |
| GET | `/api/categories/` | 分类及各分类文章数 | 否 |
| GET | `/api/tags/` | 标签 | 否 |
| GET | `/api/archive/` | 按月份统计文章数 | 否 |
| POST | `/api/auth/register/` | 注册，直接返回 token | 否 |
| POST | `/api/auth/login/` | 登录，返回 access / refresh / 用户资料 | 否 |
| POST | `/api/auth/refresh/` | 用 refresh 换新的 access | 否 |
| GET / PATCH | `/api/auth/me/` | 当前用户资料 | 是 |

列表接口支持的查询参数：

```
?page=2&page_size=10          分页
?category=django              按分类 slug 过滤
?tag=orm                      按标签 slug 过滤
?author=demo                  按作者过滤
?search=序列化器               标题/摘要/正文模糊搜索
?year=2026&month=9            按归档月份过滤
?ordering=-views              排序（-published_at / -views / title …）
?mine=1                       只看自己的文章，含草稿（需登录）
```

## 前后端分离是怎么落地的

1. **后端只管数据**：`settings.py` 里 `TEMPLATES` 现在只服务于 Django Admin，
   业务接口全部由 DRF 返回 JSON。
2. **跨域**：前端跑在 5173，后端跑在 8000，属于不同源。
   `CORS_ALLOWED_ORIGINS` 放行了前端地址（也可以改成用 Vite 的 proxy 转发，见 `vite.config.js`）。
3. **登录状态**：用 JWT。登录拿到 `access`（60 分钟）和 `refresh`（7 天），
   前端把 `access` 放进请求头 `Authorization: Bearer <token>`。
4. **自动续期**：`frontend/src/api/http.js` 的响应拦截器发现 401 时，
   会自动用 `refresh` 换新 token 再重发原请求；换不到就清空登录态跳登录页。
5. **草稿的可见性**：`?mine=1` 能看到自己的草稿，其他人访问草稿接口会被 403 拒绝——
   权限校验在后端做，前端藏按钮只是体验优化。

## 常用操作

```powershell
# 后端
python manage.py makemigrations blog    # 改了模型后生成迁移文件
python manage.py migrate                # 执行迁移
python manage.py createsuperuser        # 新建超级用户
python manage.py seed_blog --reset      # 清空文章重新生成演示数据
python manage.py shell                  # 交互式 ORM 环境

# 前端
npm run dev                             # 开发服务器（热更新）
npm run build                           # 打包到 frontend/dist
npm run preview                         # 本地预览打包结果
```

## 学习路径建议

想按顺序自己走一遍，可以照着这个顺序读代码：

1. `blog/models.py` → 数据表是怎么定义出来的（含中文 slug、多对多、自定义 Manager）
2. `python manage.py makemigrations && migrate` → 观察迁移文件长什么样
3. `blog/serializers.py` → 模型对象怎么变成 JSON，怎么校验前端提交的数据
4. `blog/views.py` → ViewSet、筛选、分页、自定义 action（评论、推荐位）、聚合查询
5. `blog/permissions.py` → 对象级权限：为什么别人改不了你的文章
6. `Learning_Log/settings.py` → CORS、JWT、DRF 全局配置
7. `frontend/src/api/` → axios 实例与两个拦截器
8. `frontend/src/views/HomeView.vue` → 列表页：URL 查询参数驱动的筛选与分页
9. `frontend/src/views/EditorView.vue` → 表单提交、Markdown 预览、文件上传（multipart）

## 还可以继续做

- 嵌套评论（`Comment` 加一个 `parent` 自关联字段）
- 文章点赞 / 收藏
- 全文搜索换成 Whoosh 或 Elasticsearch
- 用 `markdown` 库在后端渲染，前端只收 HTML
- 换成 PostgreSQL，用 `django-environ` 管理配置
- 部署：Gunicorn + Nginx，前端 `npm run build` 后交给 Nginx 托管
