"""Django Admin 配置。

前后端分离之后，Admin 就是我们最省事的「写作后台」：
登录 http://127.0.0.1:8000/admin/ 就能写文章、传封面、管理评论。
"""

from django.contrib import admin

from .models import Category, Comment, Post, Tag


@admin.register(Category)
class CategoryAdmin(admin.ModelAdmin):
    # list_display：列表页显示哪几列（可以写模型字段，也可以写下面的方法名）
    list_display = ("name", "slug", "post_count", "created_at")
    # search_fields：右上角搜索框搜哪些字段。
    # 它还有个副作用：别的 Admin 用 autocomplete_fields 指向本模型时必须先有它
    search_fields = ("name",)  # PostAdmin 的 autocomplete 需要它
    # readonly_fields：只展示、不能在这里改（slug 由模型自动生成）
    readonly_fields = ("slug", "created_at")

    # @admin.display 可以理解成"给这个方法起个后台里显示的列名"
    @admin.display(description="文章数")
    def post_count(self, obj):
        return obj.posts.count()


@admin.register(Tag)
class TagAdmin(admin.ModelAdmin):
    list_display = ("name", "slug", "post_count", "created_at")
    search_fields = ("name",)
    readonly_fields = ("slug", "created_at")

    @admin.display(description="文章数")
    def post_count(self, obj):
        return obj.posts.count()


class CommentInline(admin.TabularInline):
    """在文章编辑页里直接管理评论的内嵌表格。"""

    model = Comment
    extra = 0  # 不显示额外的空行，页面更干净
    fields = ("author", "content", "is_active", "created_at")
    readonly_fields = ("created_at",)


@admin.register(Post)
class PostAdmin(admin.ModelAdmin):
    list_display = (
        "title",
        "author",
        "category",
        "status",
        "is_featured",
        "views",
        "published_at",
    )
    list_filter = ("status", "is_featured", "category", "tags", "created_at")
    # list_editable：列表页就能直接改，发文章时不用一篇篇点进去。
    # 注意它列出的字段必须同时出现在 list_display 里
    list_editable = ("status", "is_featured")  # 列表页直接改状态，发文章更快
    search_fields = ("title", "summary", "body")
    date_hierarchy = "created_at"
    autocomplete_fields = ("category",)
    filter_horizontal = ("tags",)
    # slug 由模型根据标题自动生成，只读展示即可
    readonly_fields = ("slug", "views", "created_at", "updated_at", "published_at")
    inlines = (CommentInline,)
    fieldsets = (
        # 把字段分组显示，长表单看起来清爽很多
        ("基本信息", {"fields": ("title", "slug", "author", "category", "tags")}),
        ("内容", {"fields": ("summary", "body", "cover")}),
        ("发布设置", {"fields": ("status", "is_featured", "published_at")}),
        ("统计", {"fields": ("views", "created_at", "updated_at")}),
    )


@admin.register(Comment)
class CommentAdmin(admin.ModelAdmin):
    list_display = ("post", "author", "short_content", "is_active", "created_at")
    list_filter = ("is_active", "created_at")
    search_fields = ("content", "post__title", "author__username")
    list_editable = ("is_active",)
    readonly_fields = ("created_at",)
    # actions 是列表页左上角"操作"下拉框里的批量动作，
    # 对应下面以 @admin.action 装饰的方法
    actions = ("hide_comments", "show_comments")

    @admin.display(description="内容")
    def short_content(self, obj):
        return obj.content[:40]

    @admin.action(description="隐藏所选评论")
    def hide_comments(self, request, queryset):
        queryset.update(is_active=False)

    @admin.action(description="显示所选评论")
    def show_comments(self, request, queryset):
        queryset.update(is_active=True)
