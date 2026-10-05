"""生成演示数据，让项目一跑起来就有内容可看。

用法：
    python manage.py seed_blog            # 生成演示数据
    python manage.py seed_blog --reset    # 先清空文章/分类/标签/评论再生成
    python manage.py seed_blog --admin    # 顺便创建超级用户 admin / admin123456
"""

from datetime import timedelta

from django.contrib.auth import get_user_model
from django.core.management.base import BaseCommand
from django.db import transaction
from django.utils import timezone

from blog.models import Category, Comment, Post, Tag

User = get_user_model()

CATEGORIES = [
    ("Django", "Django 框架的模型、视图、路由与接口开发"),
    ("前端", "Vue、JavaScript 与浏览器相关笔记"),
    ("数据库", "ORM、SQL 与查询优化"),
    ("随笔", "学习过程中的思考与总结"),
]

TAGS = ["Python", "Django", "DRF", "Vue", "ORM", "JWT", "踩坑", "入门", "性能"]

POSTS = [
    {
        "title": "从零搭建个人博客：Django + Vue 前后端分离",
        "category": "Django",
        "tags": ["Django", "Vue", "入门"],
        "featured": True,
        "days_ago": 2,
        "views": 268,
        "body": """
这是一个用来练手的个人博客项目，目标很明确：**后端只出 JSON，前端只画页面**。

## 为什么要前后端分离

传统 Django 项目用模板渲染 HTML，页面和数据是揉在一起的。分离以后职责变得很清楚：

| 角色 | 负责的事情 | 技术 |
| --- | --- | --- |
| 后端 | 数据存储、业务规则、权限校验 | Django + DRF |
| 前端 | 页面、交互、路由、状态 | Vue 3 + Vite |

两者之间只靠一层 HTTP 接口沟通，接口约定好了，两边可以各自独立开发和替换。

## 后端的三个核心概念

```python
# models.py：数据结构
class Post(models.Model):
    title = models.CharField("标题", max_length=150)
    body = models.TextField("正文")

# serializers.py：接口里的数据结构
class PostListSerializer(serializers.ModelSerializer):
    class Meta:
        model = Post
        fields = ("id", "title", "summary")

# views.py：对外提供的能力
class PostViewSet(viewsets.ModelViewSet):
    queryset = Post.published.all()
    serializer_class = PostListSerializer
```

记住这条线：**模型管数据库 → 序列化器管接口 → 视图管规则**。

## 接口目录

启动后端后访问 `http://127.0.0.1:8000/api/`，DRF 会自动列出现在所有可用的接口，
可以直接在浏览器里点着调，写前端之前先用它把接口验一遍。

## 下一步

- 用 Django Admin 写第一篇文章
- 用 Vue 的 `axios` 把列表拉出来渲染
- 给详情页加上 Markdown 渲染和评论
""",
    },
    {
        "title": "Django 模型与迁移：把想法变成数据库表",
        "category": "Django",
        "tags": ["Django", "ORM", "入门"],
        "featured": False,
        "days_ago": 6,
        "views": 173,
        "body": """
写 Django 最爽的一点：你只描述「数据长什么样」，建表的事交给迁移系统。

## 一次标准的流程

```bash
python manage.py makemigrations   # 对比模型和迁移文件，生成改动脚本
python manage.py migrate          # 把改动真正执行到数据库
python manage.py showmigrations   # 看看哪些迁移已经执行过
```

`makemigrations` 生成的是 Python 脚本，**应该提交进 Git**；
它就是数据库结构的版本历史，换台机器也能一比一复原。

## 几个容易踩的坑

1. `null=True` 和 `blank=True` 不是一回事
   - `null` 是数据库层面允许为空
   - `blank` 是表单校验层面允许不填
   - 字符串字段一般只写 `blank=True`，因为 Django 约定用空字符串表示"没有"
2. `auto_now_add` / `auto_now` 的字段在后台无法手动修改
3. 迁移文件不要手动改，要改就改模型重新生成

## 中文标题的 slug 问题

`slugify("我的第一篇博客")` 会返回空字符串，因为标准 slug 只允许 ASCII。
解决办法是允许 unicode：

```python
from django.utils.text import slugify

slug = slugify(title, allow_unicode=True) or "fallback-slug"
```

这样文章地址就是 `/posts/我的第一篇博客`，可读性还不错。
""",
    },
    {
        "title": "DRF 序列化器到底在做什么",
        "category": "Django",
        "tags": ["DRF", "Django"],
        "featured": False,
        "days_ago": 10,
        "views": 214,
        "body": """
刚学 DRF 时最容易懵的就是 Serializer：它和 Model 到底啥关系？

一句话：**Model 描述数据库里的数据，Serializer 描述接口里的数据。**
两者形状很像，但目的大不相同。

## 出方向：模型对象 → JSON

```python
class PostListSerializer(serializers.ModelSerializer):
    author = UserBriefSerializer(read_only=True)
    tags = TagSerializer(many=True, read_only=True)
    comment_count = serializers.SerializerMethodField()

    class Meta:
        model = Post
        fields = ("id", "title", "summary", "author", "tags", "comment_count")

    def get_comment_count(self, obj):
        return obj.comments.filter(is_active=True).count()
```

`ModelSerializer` 会自动按模型字段生成规则，你只需要声明「要多给哪些东西」。

## 入方向：JSON → 校验 → 模型对象

`serializer.is_valid(raise_exception=True)` 会做三件事：

1. 类型转换（字符串 "3" → 整数 3）
2. 字段校验（必填、长度、唯一性）
3. 执行 `validate_<字段名>()` 和 `validate()` 里的自定义规则

## 为什么读和写要用两个序列化器

列表接口不需要正文，列表页一次返回 8 篇带正文的文章会白白浪费带宽；
而写接口需要接收正文，还要处理标签这种"字符串数组"的额外结构。

分开写以后，接口返回的数据既精确，前端处理起来也更省事。
""",
    },
    {
        "title": "JWT 登录：前端怎么保存和自动刷新 token",
        "category": "前端",
        "tags": ["JWT", "Vue", "踩坑"],
        "featured": True,
        "days_ago": 14,
        "views": 331,
        "body": """
前后端分离后，浏览器不再靠 Cookie + Session 记住登录状态，
常见方案是 **JWT（JSON Web Token）**。

## 一次完整的登录流程

1. 前端 `POST /api/auth/login/` 提交用户名和密码
2. 后端验证通过，返回两个 token：
   - `access`：短命（本项目 60 分钟），每次请求放在请求头里
   - `refresh`：长命（7 天），只用来换新的 access
3. 前端把 token 存起来，之后每个请求都带上：

```http
Authorization: Bearer eyJhbGciOiJIUzI1NiIs...
```

## access 过期了怎么办

关键技巧是拦截 401 响应，自动用 refresh 换一次新 token，然后重发原请求：

```javascript
// 响应拦截器（简化版）
if (error.response?.status === 401 && !error.config._retry) {
  error.config._retry = true
  const { data } = await axios.post('/api/auth/refresh/', { refresh })
  localStorage.setItem('access', data.access)
  return http(error.config)   // 带着新 token 重发
}
```

注意两点：

1. 加 `_retry` 标记，否则会无限循环
2. 刷新也失败（refresh 也过期了）就清空本地 token，跳回登录页

## 安全提醒

- 生产环境一定要上 HTTPS，否则 token 在网络上就是明文
- `localStorage` 有 XSS 风险，所以渲染富文本必须做 XSS 过滤
- 后端每个接口都要真正校验权限，不能只靠前端藏按钮
""",
    },
    {
        "title": "Vue 3 学习笔记：ref、reactive 和 computed",
        "category": "前端",
        "tags": ["Vue", "入门"],
        "featured": False,
        "days_ago": 20,
        "views": 145,
        "body": """
组合式 API 里最常用的三个响应式工具，先分清楚什么时候用谁。

## ref：包装一个值

```javascript
import { ref } from 'vue'

const count = ref(0)
count.value++          // 在 <script> 里要加 .value
// 在模板里可以省略：{{ count }}
```

基本类型、数组、对象都能用 ref，是最通用的选择。

## reactive：包装一个对象

```javascript
import { reactive } from 'vue'

const form = reactive({ title: '', body: '' })
form.title = '新文章'   // 不需要 .value
```

代价是不能整体替换（`form = {...}` 会丢掉响应式），也不能用于基本类型。

## computed：由别的数据算出来的数据

```javascript
import { computed, ref } from 'vue'

const page = ref(1)
const total = ref(53)
const totalPages = computed(() => Math.ceil(total.value / 8))
```

它有两个好处：**结果会被缓存**（依赖不变就不会重复算），
而且依赖变化时会自动重新计算，适合做过滤、分页、格式化。

## 我的选择习惯

- 单个值、数组 → `ref`
- 一个固定形状的表单对象 → `reactive`
- 任何"由别的数据推出来"的东西 → `computed`
- 需要在多处共享并带操作逻辑 → 放进 Pinia store
""",
    },
    {
        "title": "查询优化：select_related 和 prefetch_related 的区别",
        "category": "数据库",
        "tags": ["ORM", "性能", "踩坑"],
        "featured": False,
        "days_ago": 27,
        "views": 198,
        "body": """
列表页显示 8 篇文章，每篇都要显示作者名和标签。
如果写法不对，SQL 会执行 1 + 8 + 8 = 17 次，这就是 **N+1 查询问题**。

## 两种预加载

```python
# 多对一 / 一对一：用 select_related，走 SQL JOIN
Post.objects.select_related("author", "category")

# 多对多 / 一对多：用 prefetch_related，额外查一次再在 Python 里拼装
Post.objects.prefetch_related("tags")

# 组合使用，一次查询准备好所有要展示的数据
Post.objects.select_related("author", "category").prefetch_related("tags")
```

区别来自关系类型：`select_related` 只能用于单值关系，因为它靠 JOIN；
`prefetch_related` 处理"一个对象对应多行"的情况，靠第二条查询。

## 怎么确认真的生效了

```python
queryset = Post.objects.select_related("author").prefetch_related("tags")
for post in queryset:
    print(post.author.username, [t.name for t in post.tags.all()])
# 打开 shell 观察：只有 3 条 SQL，而不是几十条
```

## 顺带一提：计数也别硬查

```python
from django.db.models import Count, Q

Post.objects.annotate(
    comment_count=Count("comments", filter=Q(comments__is_active=True))
)
```

用 `annotate` 让数据库一次性把计数算好，比在循环里一条条 `.count()` 快得多。
""",
    },
    {
        "title": "我的学习计划：把博客当成练手项目",
        "category": "随笔",
        "tags": ["入门"],
        "featured": False,
        "days_ago": 35,
        "views": 96,
        "body": """
学一个新框架，光看文档很容易"看懂了但写不出来"。我的办法是：
**每学一节，就给这个博客加一个真实的小功能。**

## 已经完成

- [x] 项目骨架：Django 项目 + blog 应用
- [x] 数据模型：分类、标签、文章、评论
- [x] REST 接口：列表、详情、筛选、分页
- [x] Vue 前端：首页、详情页、登录注册
- [x] 写作页面：Markdown 编辑 + 图片上传

## 接下来想做的

- [ ] 归档页面（按月份浏览）
- [ ] 评论回复（嵌套评论）
- [ ] RSS 订阅
- [ ] 全文搜索换成 Whoosh 或 Elasticsearch
- [ ] 部署到服务器，用 Nginx + Gunicorn

## 一点心得

1. 先让功能跑通，再想优化。第一版丑一点完全没关系
2. 报错信息要看完整的堆栈，`DEBUG = True` 时 Django 给的提示非常详细
3. 把踩过的坑写下来，下次真的会省很多时间
""",
    },
]

COMMENTS = [
    {
        "post_title": "从零搭建个人博客：Django + Vue 前后端分离",
        "author": "demo",
        "content": "这个前后端分离的思路讲得很清楚，我跟着做了一遍，接口用 DRF 的网页版先调通再写前端，效率高很多。",
        "days_ago": 1,
    },
    {
        "post_title": "从零搭建个人博客：Django + Vue 前后端分离",
        "author": "reader",
        "content": "请问前端跨域问题怎么解决的？我之前一直卡在这里。",
        "days_ago": 1,
    },
    {
        "post_title": "从零搭建个人博客：Django + Vue 前后端分离",
        "author": "demo",
        "content": "楼上可以看后端 settings 里的 django-cors-headers 配置，把前端地址加进 CORS_ALLOWED_ORIGINS 就行。",
        "days_ago": 1,
    },
    {
        "post_title": "DRF 序列化器到底在做什么",
        "author": "reader",
        "content": "读写分离两个序列化器这点之前一直没想明白，现在懂了。",
        "days_ago": 3,
    },
    {
        "post_title": "JWT 登录：前端怎么保存和自动刷新 token",
        "author": "reader",
        "content": "拦截器那段代码很实用，加 _retry 标记确实能避免死循环。",
        "days_ago": 5,
    },
]


class Command(BaseCommand):
    """自定义管理命令：python manage.py seed_blog

    写一个命令比在 shell 里手敲几十行强得多 —— 换台机器、重装数据库后
    一条命令就能把演示环境恢复原样。
    """

    help = "生成博客的演示数据（用户、分类、标签、文章、评论）"

    def add_arguments(self, parser):
        # 这两个开关就是命令行里的 --reset 和 --admin
        parser.add_argument("--reset", action="store_true", help="先清空文章、分类、标签和评论")
        parser.add_argument("--admin", action="store_true", help="同时创建超级用户 admin / admin123456")

    @transaction.atomic
    def handle(self, *args, **options):
        # @transaction.atomic 保证整段过程是一个事务：
        # 中途报错就全部回滚，不会留下"用户建了但文章没建"的半成品
        if options["reset"]:
            # 删除顺序有讲究：先删引用方（评论 → 文章），再删被引用方（标签、分类）
            Comment.objects.all().delete()
            Post.objects.all().delete()
            Tag.objects.all().delete()
            Category.objects.all().delete()
            self.stdout.write(self.style.WARNING("已清空旧的文章、分类、标签和评论"))

        # 1) 用户
        authors = {}
        for username, password, email in (
            ("demo", "demo12345", "demo@example.com"),
            ("reader", "reader12345", "reader@example.com"),
        ):
            # get_or_create 让命令可以反复执行：已存在就复用，不会重复建号
            user, created = User.objects.get_or_create(
                username=username, defaults={"email": email}
            )
            if created:
                # set_password 负责把明文密码哈希后再存进数据库
                user.set_password(password)
                user.save()
                self.stdout.write(f"创建用户 {username}（密码 {password}）")
            authors[username] = user

        if options["admin"]:
            admin, created = User.objects.get_or_create(
                username="admin",
                defaults={"email": "admin@example.com", "is_staff": True, "is_superuser": True},
            )
            admin.is_staff = True
            admin.is_superuser = True
            admin.set_password("admin123456")
            admin.save()
            self.stdout.write(
                self.style.SUCCESS("超级用户已就绪：admin / admin123456（http://127.0.0.1:8000/admin/）")
            )

        # 2) 分类与标签
        categories = {}
        for name, description in CATEGORIES:
            # defaults 只在"新建"时生效，已存在的记录不会被覆盖
            category, _ = Category.objects.get_or_create(
                name=name, defaults={"description": description}
            )
            categories[name] = category

        # 字典推导式：{标签名: 标签对象}，后面按名字取用
        tags = {name: Tag.objects.get_or_create(name=name)[0] for name in TAGS}

        # 3) 文章
        demo = authors["demo"]
        now = timezone.now()
        created_posts = []
        for index, item in enumerate(POSTS, start=1):
            post, created = Post.objects.get_or_create(
                title=item["title"],
                defaults={
                    "author": demo,
                    "category": categories[item["category"]],
                    "body": item["body"].strip(),
                    "status": Post.Status.PUBLISHED,
                    "is_featured": item["featured"],
                },
            )
            # 即使文章早就存在，也把分类/状态/置顶更新成当前脚本里的设定，
            # 这样改了脚本再跑一次，数据也会跟着变
            post.category = categories[item["category"]]
            post.status = Post.Status.PUBLISHED
            post.is_featured = item["featured"]
            post.summary = ""  # 清空后由模型 save() 自动生成摘要
            post.save()
            post.tags.set([tags[name] for name in item["tags"]])

            # created_at 是 auto_now_add，正常 save() 改不动它，
            # 所以只能用 queryset.update() 绕过模型、直接写数据库，
            # 好让演示数据的时间分布看起来自然（几天前、几周前各有文章）
            published = now - timedelta(days=item["days_ago"], hours=index)
            Post.objects.filter(pk=post.pk).update(
                published_at=published, created_at=published, views=item["views"]
            )
            created_posts.append(post)
            if created:
                self.stdout.write(f"创建文章：{post.title}")

        # 4) 评论
        for item in COMMENTS:
            # 评论挂在文章上，找不到对应文章就跳过
            post = next((p for p in created_posts if p.title == item["post_title"]), None)
            if post is None:
                continue
            Comment.objects.get_or_create(
                post=post,
                author=authors[item["author"]],
                content=item["content"],
                defaults={"created_at": now - timedelta(days=item["days_ago"])},
            )

        self.stdout.write(
            self.style.SUCCESS(
                f"演示数据完成：{Category.objects.count()} 个分类、"
                f"{Tag.objects.count()} 个标签、{Post.objects.count()} 篇文章、"
                f"{Comment.objects.count()} 条评论"
            )
        )
