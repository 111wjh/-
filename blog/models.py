"""博客数据模型。

学习要点：Django 里一个「模型类」= 数据库里一张表。
写完模型后执行
    python manage.py makemigrations
    python manage.py migrate
Django 会自动生成建表语句并执行，你不用手写 CREATE TABLE。
"""

import math
import re
import uuid

from django.conf import settings
from django.db import models
from django.utils import timezone
from django.utils.text import slugify


def build_unique_slug(model, value, *, instance=None, field_name="slug", max_length=180):
    """根据标题生成唯一的 URL 标识（slug）。

    注意：默认的 slugify("我的第一篇博客") 结果是空字符串，
    因为标准 slug 只允许 ASCII 字符。所以这里 allow_unicode=True，
    让中文标题也能变成可读的网址；遇到重复再追加 -2、-3。
    """
    base = slugify(value, allow_unicode=True)[:max_length] or uuid.uuid4().hex[:8]
    queryset = model.objects.all()
    if instance is not None and instance.pk:
        queryset = queryset.exclude(pk=instance.pk)

    slug = base
    index = 2
    while queryset.filter(**{field_name: slug}).exists():
        slug = f"{base}-{index}"
        index += 1
    return slug


class Category(models.Model):
    """文章分类，例如「Python」「Django」「随笔」。"""

    name = models.CharField("名称", max_length=50, unique=True)
    slug = models.SlugField(
        "URL 标识", max_length=60, unique=True, allow_unicode=True, blank=True
    )
    description = models.CharField("描述", max_length=200, blank=True)
    created_at = models.DateTimeField("创建时间", auto_now_add=True)

    class Meta:
        verbose_name = "分类"
        verbose_name_plural = "分类"
        ordering = ["name"]

    def __str__(self):
        return self.name

    def save(self, *args, **kwargs):
        if not self.slug:
            self.slug = build_unique_slug(
                Category, self.name, instance=self, max_length=60
            )
        super().save(*args, **kwargs)


class Tag(models.Model):
    """文章标签，一篇文章可以有多个标签（多对多关系）。"""

    name = models.CharField("名称", max_length=30, unique=True)
    slug = models.SlugField(
        "URL 标识", max_length=60, unique=True, allow_unicode=True, blank=True
    )
    created_at = models.DateTimeField("创建时间", auto_now_add=True)

    class Meta:
        verbose_name = "标签"
        verbose_name_plural = "标签"
        ordering = ["name"]

    def __str__(self):
        return self.name

    def save(self, *args, **kwargs):
        if not self.slug:
            self.slug = build_unique_slug(Tag, self.name, instance=self, max_length=60)
        super().save(*args, **kwargs)


class PublishedManager(models.Manager):
    """自定义管理器：Post.published.all() 只返回已发布的文章。

    学习要点：Manager 是「表级查询入口」，把常用的过滤条件封装进去，
    就不用到处重复写 filter(status=...)。
    """

    def get_queryset(self):
        return super().get_queryset().filter(status=Post.Status.PUBLISHED)


class Post(models.Model):
    """博客文章。"""

    class Status(models.TextChoices):
        # TextChoices 是 Django 提供的枚举写法：
        # 左边是存进数据库的值，右边是后台/接口里显示的文案
        DRAFT = "draft", "草稿"
        PUBLISHED = "published", "已发布"

    # CharField 对应 VARCHAR；引号里第一个参数是给后台看的字段名（verbose_name）
    title = models.CharField("标题", max_length=150)
    # blank=True 表示"表单里可以不填"，保存时会由下面的 save() 自动生成
    # unique=True 让数据库层面也保证不重复，两个请求同时生成也不会撞车
    slug = models.SlugField(
        "URL 标识", max_length=200, unique=True, allow_unicode=True, blank=True
    )
    # 外键：一篇文章属于一个用户。
    # on_delete=CASCADE 表示用户被删时，他的文章一起删掉；
    # related_name="posts" 让反向查询写成 user.posts.all()
    author = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        verbose_name="作者",
        on_delete=models.CASCADE,
        related_name="posts",
    )
    # 分类是可选的：on_delete=SET_NULL 表示分类被删时，文章保留但分类置空
    category = models.ForeignKey(
        Category,
        verbose_name="分类",
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="posts",
    )
    # 多对多：一篇文章多个标签，一个标签也属于多篇文章。
    # Django 会自动创建中间表 blog_post_tags 来存这种关系
    tags = models.ManyToManyField(
        Tag, verbose_name="标签", blank=True, related_name="posts"
    )
    summary = models.TextField("摘要", max_length=300, blank=True)
    body = models.TextField("正文（Markdown）")
    # 图片专用字段，需要安装 Pillow；upload_to 决定文件存到 media/covers/年/月/ 下
    cover = models.ImageField("封面图", upload_to="covers/%Y/%m/", blank=True)
    # choices 限制只能填 draft / published 两个值，后台会自动变成下拉框
    status = models.CharField(
        "状态", max_length=10, choices=Status.choices, default=Status.DRAFT
    )
    is_featured = models.BooleanField("置顶推荐", default=False)
    # PositiveIntegerField 不允许负数，阅读量不可能小于 0
    views = models.PositiveIntegerField("阅读量", default=0)
    # auto_now_add：只在创建时自动写入；auto_now：每次保存都更新
    created_at = models.DateTimeField("创建时间", auto_now_add=True)
    updated_at = models.DateTimeField("更新时间", auto_now=True)
    # 草稿还没有发布时间，所以允许为空
    published_at = models.DateTimeField("发布时间", null=True, blank=True)

    # 两个管理器：objects 是全部文章，published 只含已发布的
    objects = models.Manager()
    published = PublishedManager()

    class Meta:
        # verbose_name 决定 Django Admin 里显示的中文名
        verbose_name = "文章"
        verbose_name_plural = "文章"
        # 默认排序：置顶在前，然后按发布时间倒序（最新的在前）
        ordering = ["-is_featured", "-published_at", "-created_at"]
        # 给常用查询加索引，数据量大了之后列表页不会慢
        indexes = [
            models.Index(fields=["-published_at"]),
            models.Index(fields=["status", "-published_at"]),
        ]

    def __str__(self):
        return self.title

    def save(self, *args, **kwargs):
        # 这里是"模型钩子"的典型用法：把生成规则集中在一处，
        # 不管从 Admin、接口还是脚本创建文章，都能自动补上这些字段
        if not self.slug:
            self.slug = build_unique_slug(Post, self.title, instance=self)
        if not self.summary:
            self.summary = self.build_summary()
        # 第一次发布时记录发布时间
        if self.status == self.Status.PUBLISHED and self.published_at is None:
            self.published_at = timezone.now()
        super().save(*args, **kwargs)

    def build_summary(self, length=120):
        """从 Markdown 正文里粗略抽出一段纯文本摘要。"""
        # 几行正则把代码块、图片、链接、Markdown 符号去掉，只留纯文字
        text = re.sub(r"```.*?```", " ", self.body or "", flags=re.S)
        text = re.sub(r"!\[[^\]]*\]\([^)]*\)", " ", text)  # 去掉图片
        text = re.sub(r"\[([^\]]*)\]\([^)]*\)", r"\1", text)  # 链接只留文字
        text = re.sub(r"[#>*`_~\-]", " ", text)
        text = re.sub(r"\s+", " ", text).strip()
        return text[:length]

    @property
    def reading_minutes(self):
        """估算阅读时长：中文按 400 字/分钟，英文单词按 200 个/分钟。"""
        # @property 让它可以像普通字段一样访问：post.reading_minutes
        # 这样序列化器里写 reading_minutes = IntegerField(read_only=True) 就能直接读
        text = self.body or ""
        chinese = sum(1 for char in text if "\u4e00" <= char <= "\u9fff")
        words = len(re.findall(r"[A-Za-z0-9']+", text))
        return max(1, math.ceil(chinese / 400 + words / 200))


class Comment(models.Model):
    """文章评论（登录后才能发表）。"""

    # on_delete=CASCADE：文章被删时，它下面的评论一起删掉
    post = models.ForeignKey(
        Post, verbose_name="文章", on_delete=models.CASCADE, related_name="comments"
    )
    # 这里用 SET_NULL：用户注销后，评论保留但作者字段置空，
    # 界面上显示成"已注销用户"（见下面的 author_name）
    author = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        verbose_name="评论者",
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="comments",
    )
    content = models.TextField("内容", max_length=500)
    # 用开关代替删除，管理后台可以「隐藏」不当评论
    is_active = models.BooleanField("显示", default=True)
    created_at = models.DateTimeField("评论时间", auto_now_add=True)

    class Meta:
        verbose_name = "评论"
        verbose_name_plural = "评论"
        ordering = ["-created_at"]

    def __str__(self):
        return f"{self.author_name}：{self.content[:20]}"

    @property
    def author_name(self):
        return self.author.username if self.author else "已注销用户"
