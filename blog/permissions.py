"""自定义权限类。

学习要点：DRF 的权限分成两级 ——
  * 视图级（has_permission）：能不能访问这个接口，例如"没登录不能发评论"
  * 对象级（has_object_permission）：能不能操作这一条数据，例如"只能改自己的文章"
"""

from rest_framework import permissions

from .models import Post


class IsAuthorOrReadOnly(permissions.BasePermission):
    """所有人都能读已发布的内容；只有作者本人或管理员能改。"""

    message = "你只能修改或删除自己写的文章。"

    def has_object_permission(self, request, view, obj):
        # SAFE_METHODS = GET / HEAD / OPTIONS，也就是"只读请求"
        if request.method in permissions.SAFE_METHODS:
            # 草稿属于私密内容：只有作者和管理员能看到
            if getattr(obj, "status", None) == Post.Status.DRAFT:
                return bool(
                    request.user.is_authenticated
                    and (request.user.is_staff or obj.author_id == request.user.id)
                )
            return True

        return bool(
            # 注意：没登录时 request.user 是 AnonymousUser，访问 .id 会报错，
            # 所以要先判断 is_authenticated
            request.user.is_authenticated
            and (request.user.is_staff or getattr(obj, "author_id", None) == request.user.id)
        )


class IsCommentOwner(permissions.BasePermission):
    """评论：只有评论者本人或管理员能删除。"""

    message = "你只能删除自己的评论。"

    def has_object_permission(self, request, view, obj):
        return bool(
            request.user.is_authenticated
            and (request.user.is_staff or obj.author_id == request.user.id)
        )
