"""序列化器（Serializer）。

学习要点：Serializer 是 DRF 的核心，它负责两件事 ——
  1. 出：把数据库里的模型对象翻译成 JSON 或 Python 字典
  2. 入：校验前端提交的数据，再转换成模型对象存进数据库
一句话：模型管数据库，序列化器管「接口里的数据长什么样」。
"""

from django.contrib.auth import get_user_model
from django.contrib.auth.password_validation import validate_password
from django.db import transaction
from rest_framework import serializers
from rest_framework_simplejwt.serializers import TokenObtainPairSerializer

from .models import Category, Comment, Post, Tag

User = get_user_model()


class UserBriefSerializer(serializers.ModelSerializer):
    """作者信息只暴露 id 和用户名，不要把邮箱、权限等泄露给所有人。"""

    class Meta:
        model = User
        # ModelSerializer 会自动按模型字段生成校验规则，你只要挑出要暴露的字段
        fields = ("id", "username")


class UserSerializer(serializers.ModelSerializer):
    """当前登录用户的完整资料（/api/auth/me/）。"""

    post_count = serializers.SerializerMethodField()

    class Meta:
        model = User
        fields = (
            "id",
            "username",
            "email",
            "first_name",
            "last_name",
            "is_staff",
            "date_joined",
            "post_count",
        )
        read_only_fields = ("id", "username", "is_staff", "date_joined")

    def get_post_count(self, obj):
        # obj 就是当前正在序列化的用户对象
        return obj.posts.filter(status=Post.Status.PUBLISHED).count()


class RegisterSerializer(serializers.ModelSerializer):
    """注册新用户。"""

    # write_only=True：这个字段只用于接收数据，绝不会出现在返回的 JSON 里（密码同理）
    password = serializers.CharField(
        write_only=True,
        min_length=8,
        style={"input_type": "password"},
        label="密码",
        help_text="至少 8 位，不能是纯数字或常见弱口令",
    )
    password_confirm = serializers.CharField(
        write_only=True, style={"input_type": "password"}, label="确认密码"
    )

    class Meta:
        model = User
        fields = ("id", "username", "email", "password", "password_confirm")

    def validate(self, attrs):
        # attrs 是所有字段校验通过后的字典，可以在这里做跨字段的校验。
        # pop 出确认密码，免得把它也传进 create_user
        if attrs["password"] != attrs.pop("password_confirm"):
            raise serializers.ValidationError({"password_confirm": "两次输入的密码不一致。"})
        # 复用 Django 自带的密码强度校验（settings.AUTH_PASSWORD_VALIDATORS）
        validate_password(attrs["password"])
        return attrs

    def create(self, validated_data):
        # create_user 会自动把密码哈希后存储，绝不保存明文
        return User.objects.create_user(**validated_data)


class LoginSerializer(TokenObtainPairSerializer):
    """登录：除了 access / refresh 两个 token，额外返回用户资料，省一次请求。"""

    def validate(self, attrs):
        data = super().validate(attrs)
        data["user"] = UserSerializer(self.user).data
        return data


class CategorySerializer(serializers.ModelSerializer):
    # SerializerMethodField 的值来自下面 get_<字段名>() 方法的返回值，
    # 适合"数据库里没有、需要算一下"的字段
    post_count = serializers.SerializerMethodField()

    class Meta:
        model = Category
        fields = ("id", "name", "slug", "description", "post_count")
        read_only_fields = ("id", "slug")

    def get_post_count(self, obj):
        # 优先用查询集 annotate 好的值（一次 SQL 算完全部），
        # 只有在没有注解时才退化成一条条 count，避免 N+1
        annotated = getattr(obj, "published_post_count", None)
        if annotated is not None:
            return annotated
        return obj.posts.filter(status=Post.Status.PUBLISHED).count()


class CategoryBriefSerializer(serializers.ModelSerializer):
    class Meta:
        model = Category
        fields = ("id", "name", "slug")


class TagSerializer(serializers.ModelSerializer):
    post_count = serializers.SerializerMethodField()

    class Meta:
        model = Tag
        fields = ("id", "name", "slug", "post_count")
        read_only_fields = ("id", "slug")

    def get_post_count(self, obj):
        annotated = getattr(obj, "published_post_count", None)
        if annotated is not None:
            return annotated
        return obj.posts.filter(status=Post.Status.PUBLISHED).count()


class PostListSerializer(serializers.ModelSerializer):
    """列表用的轻量结构：不含正文，减小响应体积。"""

    # 嵌套序列化器：把外键、多对多展开成对象，而不是只给一个 id
    author = UserBriefSerializer(read_only=True)
    category = CategoryBriefSerializer(read_only=True)
    tags = TagSerializer(many=True, read_only=True)
    comment_count = serializers.SerializerMethodField()
    reading_minutes = serializers.IntegerField(read_only=True)

    class Meta:
        model = Post
        fields = (
            "id",
            "title",
            "slug",
            "summary",
            "cover",
            "author",
            "category",
            "tags",
            "status",
            "is_featured",
            "views",
            "reading_minutes",
            "comment_count",
            "created_at",
            "updated_at",
            "published_at",
        )

    def get_comment_count(self, obj):
        # 视图里用 annotate 算过一次就不重复查数据库
        annotated = getattr(obj, "comment_count", None)
        if annotated is not None:
            return annotated
        return obj.comments.filter(is_active=True).count()


class PostDetailSerializer(PostListSerializer):
    """详情结构：多一个 body（Markdown 正文）。"""

    class Meta(PostListSerializer.Meta):
        fields = PostListSerializer.Meta.fields + ("body",)


class PostWriteSerializer(serializers.ModelSerializer):
    """写文章 / 改文章时使用的结构。

    设计小技巧：分类用 category_id 传 id，标签用 tag_names 传字符串数组，
    前端拼表单最省事 —— 传 ["Django", "踩坑"] 就行，后端自动创建不存在的标签。
    """

    # 作者由后端赋值，前端只能读
    author = UserBriefSerializer(read_only=True)
    # 前端传 category_id（数字），source 告诉 DRF 它其实要写进 category 字段；
    # allow_null=True 让"不分类"也能提交
    category_id = serializers.PrimaryKeyRelatedField(
        queryset=Category.objects.all(),
        source="category",
        required=False,
        allow_null=True,
        label="分类 id",
    )
    # ListField 表示接收一个数组，write_only 说明只进不出；
    # 标签名不存在时由下面的 _sync_tags 自动创建
    tag_names = serializers.ListField(
        child=serializers.CharField(max_length=30),
        required=False,
        write_only=True,
        label="标签名列表",
    )
    tags = TagSerializer(many=True, read_only=True)

    class Meta:
        model = Post
        fields = (
            "id",
            "title",
            "slug",
            "summary",
            "body",
            "cover",
            "status",
            "is_featured",
            "category_id",
            "tag_names",
            "tags",
            "author",
            "created_at",
            "updated_at",
            "published_at",
        )
        read_only_fields = ("id", "slug", "created_at", "updated_at", "published_at")

    @transaction.atomic
    def create(self, validated_data):
        # 标签不是模型的直接字段，先取出来，等文章存好拿到 id 再写中间表
        tag_names = validated_data.pop("tag_names", [])
        post = super().create(validated_data)
        self._sync_tags(post, tag_names)
        return post

    @transaction.atomic
    def update(self, instance, validated_data):
        # 只有前端显式传了 tag_names 才覆盖标签，避免 PATCH 时误清空
        tag_names = validated_data.pop("tag_names", None)
        post = super().update(instance, validated_data)
        if tag_names is not None:
            self._sync_tags(post, tag_names)
        return post

    @staticmethod
    def _sync_tags(post, tag_names):
        """把"标签名列表"变成真正的标签对象，并绑定到文章上。"""
        tags = []
        for name in tag_names:
            name = name.strip()
            if not name:
                continue
            tag, _created = Tag.objects.get_or_create(name=name)  # slug 在模型 save() 里生成
            tags.append(tag)
        post.tags.set(tags)


class CommentSerializer(serializers.ModelSerializer):
    # 作者只读：评论者由后端从登录令牌里取，前端传什么都不算数
    author = UserBriefSerializer(read_only=True)
    is_owner = serializers.SerializerMethodField()

    class Meta:
        model = Comment
        fields = ("id", "author", "content", "created_at", "is_owner")
        read_only_fields = ("id", "author", "created_at")

    def get_is_owner(self, obj):
        """告诉前端「这条评论是不是我发的」，用来决定要不要显示删除按钮。"""
        request = self.context.get("request")
        return bool(
            request
            and request.user.is_authenticated
            and obj.author_id == request.user.id
        )

    def validate_content(self, value):
        value = value.strip()
        if len(value) < 2:
            raise serializers.ValidationError("评论至少写 2 个字。")
        if len(value) > 500:
            raise serializers.ValidationError("评论最多 500 个字。")
        return value
