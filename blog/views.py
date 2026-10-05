"""接口视图（ViewSet）。

学习要点：DRF 的 ViewSet 把一组相关接口收在一个类里，
配合 DefaultRouter 自动生成路由，代码量比一个个写 APIView 少很多。
这个文件就是「后端对外提供哪些服务」的清单。
"""

from django.contrib.auth import get_user_model
from django.db.models import Count, F, Q
from django.db.models.functions import TruncMonth
from rest_framework import generics, mixins, status, viewsets
from rest_framework.decorators import action
from rest_framework.permissions import (
    AllowAny,
    IsAdminUser,
    IsAuthenticated,
    IsAuthenticatedOrReadOnly,
)
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework_simplejwt.tokens import RefreshToken
from rest_framework_simplejwt.views import TokenObtainPairView

from . import serializers
from .models import Category, Comment, Post, Tag
from .permissions import IsAuthorOrReadOnly, IsCommentOwner

User = get_user_model()

# 允许前端指定的排序字段，白名单以外的一律忽略（防止乱传字段拖慢查询）
ALLOWED_ORDERING = {
    "-published_at",
    "published_at",
    "-created_at",
    "created_at",
    "-updated_at",
    "updated_at",
    "-views",
    "views",
    "-title",
    "title",
}


class PostViewSet(viewsets.ModelViewSet):
    """文章接口。

    GET    /api/posts/                     列表：搜索、筛选、排序、分页
    POST   /api/posts/                     新建（需登录）
    GET    /api/posts/<slug>/              详情（阅读量 +1）
    PUT/PATCH /api/posts/<slug>/           修改（仅作者本人或管理员）
    DELETE /api/posts/<slug>/              删除（仅作者本人或管理员）
    GET/POST /api/posts/<slug>/comments/   评论列表 / 发表评论
    GET    /api/posts/featured/            首页置顶推荐
    """

    lookup_field = "slug"
    lookup_value_regex = "[^/]+"  # slug 是中文，不能沿用默认的 [^/.]+
    # 两个权限一起用：IsAuthenticatedOrReadOnly 管"能不能进这个接口"，
    # IsAuthorOrReadOnly 管"这条数据你能不能改"
    permission_classes = [IsAuthenticatedOrReadOnly, IsAuthorOrReadOnly]

    # ---------- 查询集：先筛选好数据，再由序列化器翻译成 JSON ----------
    def get_queryset(self):
        queryset = (
            Post.objects.select_related("author", "category")
            .prefetch_related("tags")
            .annotate(comment_count=Count("comments", filter=Q(comments__is_active=True)))
        )

        # 草稿只有作者自己看得到
        if self.action == "list":
            mine = self.request.query_params.get("mine") in ("1", "true", "yes")
            if mine and self.request.user.is_authenticated:
                queryset = queryset.filter(author=self.request.user)
            else:
                queryset = queryset.filter(status=Post.Status.PUBLISHED)

        params = self.request.query_params

        category = params.get("category")
        if category:
            queryset = queryset.filter(category__slug=category)

        tag = params.get("tag")
        if tag:
            queryset = queryset.filter(tags__slug=tag)

        author = params.get("author")
        if author:
            queryset = queryset.filter(author__username=author)

        search = params.get("search")
        if search:
            queryset = queryset.filter(
                Q(title__icontains=search)
                | Q(summary__icontains=search)
                | Q(body__icontains=search)
            )

        year, month = params.get("year"), params.get("month")
        if year:
            queryset = queryset.filter(published_at__year=year)
        if month:
            queryset = queryset.filter(published_at__month=month)

        ordering = params.get("ordering")
        if ordering in ALLOWED_ORDERING:
            queryset = queryset.order_by(ordering)

        return queryset.distinct()

    def get_serializer_class(self):
        # 同一个 ViewSet 在不同动作下用不同结构：
        # 列表要轻、详情要全、写入要能校验
        if self.action == "list":
            return serializers.PostListSerializer
        if self.action == "retrieve":
            return serializers.PostDetailSerializer
        return serializers.PostWriteSerializer

    # ---------- 详情：顺便累加阅读量 ----------
    def retrieve(self, request, *args, **kwargs):
        instance = self.get_object()
        # 用 SQL 层的 F("views") + 1 更新，避免并发时互相覆盖
        Post.objects.filter(pk=instance.pk).update(views=F("views") + 1)
        instance.views += 1
        return Response(self.get_serializer(instance).data)

    # ---------- 新建 / 修改：返回详情结构，方便前端直接用 ----------
    def create(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        # 作者不从请求体里取，而是取当前登录用户，避免有人伪造成别人发文章
        post = serializer.save(author=request.user)
        detail = serializers.PostDetailSerializer(
            post, context=self.get_serializer_context()
        )
        return Response(
            detail.data,
            status=status.HTTP_201_CREATED,
            headers=self.get_success_headers(detail.data),
        )

    def update(self, request, *args, **kwargs):
        # partial=True 就是 PATCH：只校验、只修改前端传过来的字段
        partial = kwargs.pop("partial", False)
        instance = self.get_object()
        serializer = self.get_serializer(instance, data=request.data, partial=partial)
        serializer.is_valid(raise_exception=True)
        post = serializer.save()
        detail = serializers.PostDetailSerializer(
            post, context=self.get_serializer_context()
        )
        return Response(detail.data)

    # ---------- 自定义动作：评论 ----------
    @action(
        detail=True,
        methods=["get", "post"],
        url_path="comments",
        # 单独放宽权限：评论只要登录就能发，不该受"文章只能作者改"的限制
        permission_classes=[IsAuthenticatedOrReadOnly],
    )
    def comments(self, request, slug=None):
        # get_object() 会顺带跑对象级权限校验（草稿别人看不到）
        post = self.get_object()

        if request.method == "POST":
            serializer = serializers.CommentSerializer(
                data=request.data, context=self.get_serializer_context()
            )
            serializer.is_valid(raise_exception=True)
            serializer.save(post=post, author=request.user)
            return Response(serializer.data, status=status.HTTP_201_CREATED)

        queryset = post.comments.filter(is_active=True).select_related("author")
        # 让评论列表复用全局分页配置，返回结构和文章列表一致
        page = self.paginate_queryset(queryset)
        context = self.get_serializer_context()
        if page is not None:
            serializer = serializers.CommentSerializer(page, many=True, context=context)
            return self.get_paginated_response(serializer.data)
        serializer = serializers.CommentSerializer(queryset, many=True, context=context)
        return Response(serializer.data)

    # ---------- 自定义动作：首页推荐位 ----------
    @action(detail=False, methods=["get"], url_path="featured")
    def featured(self, request):
        # [:5] 是 SQL 的 LIMIT 5，只取前 5 条置顶文章
        queryset = self.get_queryset().filter(is_featured=True)[:5]
        serializer = serializers.PostListSerializer(
            queryset, many=True, context=self.get_serializer_context()
        )
        return Response(serializer.data)


class CategoryViewSet(viewsets.ModelViewSet):
    """分类：所有人可读，只有管理员能增删改（用 Django Admin 维护即可）。"""

    serializer_class = serializers.CategorySerializer
    lookup_field = "slug"
    lookup_value_regex = "[^/]+"

    def get_queryset(self):
        return Category.objects.annotate(
            published_post_count=Count(
                "posts", filter=Q(posts__status=Post.Status.PUBLISHED)
            )
        )

    def get_permissions(self):
        # 读接口（GET/HEAD/OPTIONS）完全开放，写接口只留给管理员
        if self.request.method in ("GET", "HEAD", "OPTIONS"):
            return [AllowAny()]
        return [IsAdminUser()]


class TagViewSet(viewsets.ModelViewSet):
    """标签：规则同分类。"""

    serializer_class = serializers.TagSerializer
    lookup_field = "slug"
    lookup_value_regex = "[^/]+"

    def get_queryset(self):
        return Tag.objects.annotate(
            published_post_count=Count(
                "posts", filter=Q(posts__status=Post.Status.PUBLISHED)
            )
        )

    def get_permissions(self):
        if self.request.method in ("GET", "HEAD", "OPTIONS"):
            return [AllowAny()]
        return [IsAdminUser()]


class CommentViewSet(viewsets.GenericViewSet, mixins.DestroyModelMixin):
    """评论只开放一个删除接口：DELETE /api/comments/<id>/（作者本人或管理员）。"""

    # 只混入 DestroyModelMixin，所以这个 ViewSet 天生没有列表和创建接口
    queryset = Comment.objects.select_related("author")
    serializer_class = serializers.CommentSerializer
    permission_classes = [IsAuthenticated, IsCommentOwner]


class RegisterView(generics.CreateAPIView):
    """注册：POST /api/auth/register/，注册成功直接返回 token，省一次登录。"""

    serializer_class = serializers.RegisterSerializer
    permission_classes = [AllowAny]

    def create(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        user = serializer.save()
        # 注册完直接签发令牌，前端拿了就能用，不用再跳一次登录
        refresh = RefreshToken.for_user(user)
        return Response(
            {
                "user": serializers.UserSerializer(user).data,
                "access": str(refresh.access_token),
                "refresh": str(refresh),
            },
            status=status.HTTP_201_CREATED,
        )


class LoginView(TokenObtainPairView):
    """登录：POST /api/auth/login/，返回 access + refresh + 用户资料。"""

    serializer_class = serializers.LoginSerializer


class MeView(generics.RetrieveUpdateAPIView):
    """当前用户：GET /api/auth/me/ 读取，PATCH 修改昵称、邮箱。"""

    serializer_class = serializers.UserSerializer
    permission_classes = [IsAuthenticated]

    def get_object(self):
        # /auth/me/ 不需要 id 参数，永远操作"当前登录的那个人"
        return self.request.user


class ArchiveView(APIView):
    """归档统计：GET /api/archive/ 返回 [{year, month, count}, ...]

    这里演示 ORM 的聚合查询：TruncMonth 把发布时间截断到「月份」再分组计数。
    """

    permission_classes = [AllowAny]

    def get(self, request):
        # TruncMonth 把 published_at 截断到月，再按它分组计数，
        # 相当于 SQL 里的 GROUP BY strftime('%Y-%m', published_at)
        rows = (
            Post.published.annotate(month=TruncMonth("published_at"))
            .values("month")
            .annotate(count=Count("id"))
            .order_by("-month")
        )
        return Response(
            [
                {
                    "year": row["month"].year,
                    "month": row["month"].month,
                    "count": row["count"],
                }
                for row in rows
                if row["month"] is not None
            ]
        )
