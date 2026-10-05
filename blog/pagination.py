"""分页配置。

学习要点：列表接口一定要分页，否则文章一多，一次把上千条记录塞给前端，
数据库、网络、浏览器都会变慢。
"""

from rest_framework.pagination import PageNumberPagination


class StandardPagination(PageNumberPagination):
    """默认每页 8 条，前端可以用 ?page=2&page_size=20 覆盖。"""

    page_size = 8  # 默认一页多少条
    page_size_query_param = "page_size"  # 允许前端用 ?page_size= 覆盖默认值
    max_page_size = 50  # 但最多给 50 条，防止有人一次拉走整张表
