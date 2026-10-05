"""自动化测试。

Django 自带测试框架，不需要额外安装任何东西：

    python manage.py test            # 跑全部测试
    python manage.py test blog       # 只跑这个应用

写测试的基本套路（每个测试方法都以 test_ 开头，Django 会自动发现）：

    from django.test import TestCase

    class PostApiTests(TestCase):
        def test_anonymous_only_sees_published_posts(self):
            # 1) 造数据：建一个用户、一篇草稿、一篇已发布
            # 2) 发请求：self.client.get("/api/posts/")
            # 3) 断言结果：self.assertEqual(response.json()["count"], 1)

建议优先给这几件事补测试，它们最容易在改动中被悄悄弄坏：
  1. 草稿的可见性（匿名看不到、作者看得到）
  2. 别人能不能修改/删除你的文章（应该返回 403）
  3. 发表评论需要登录、删除只能删自己的
  4. 阅读量自增

注意：跑了测试之后数据库不会留下垃圾数据 —— Django 会自动建一个临时库，
测试结束就销毁。
"""

# 真正写测试时把下面这行保留，TestCase 提供了 self.client 和事务隔离
# from django.test import TestCase
