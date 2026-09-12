"""
响应数据模型
"""

from dataclasses import dataclass, field
from typing import Optional, Any


@dataclass
class ApiResponse:
    """API 响应基类"""
    err_no: int = 0
    err_msg: str = ""
    
    @property
    def success(self) -> bool:
        return self.err_no == 0


def _payload(raw: Any) -> Any:
    """取出响应体的 data。出错时 data 可能是 None 或空字符串，不是 dict。"""
    if not isinstance(raw, dict):
        return None
    return raw.get("data")


def _data_dict(raw: Any) -> dict:
    d = _payload(raw)
    return d if isinstance(d, dict) else {}


def _data_list(raw: Any) -> list:
    """列表接口的 data 通常是 list，也可能被包在 data/list 字段里。"""
    d = _payload(raw)
    if isinstance(d, list):
        return d
    if isinstance(d, dict):
        for key in ("data", "list", "items"):
            v = d.get(key)
            if isinstance(v, list):
                return v
    return []


def _total(raw: Any) -> int:
    """分页总数：有的接口放在顶层，有的放在 data 里。"""
    if not isinstance(raw, dict):
        return 0
    if isinstance(raw.get("count"), int):
        return raw["count"]
    d = _payload(raw)
    if isinstance(d, dict) and isinstance(d.get("count"), int):
        return d["count"]
    return 0


@dataclass
class CreateDraftResponse(ApiResponse):
    """创建草稿响应"""
    draft_id: str = ""
    article_id: str = ""

    @classmethod
    def from_dict(cls, data: dict) -> "CreateDraftResponse":
        payload = _data_dict(data)
        return cls(
            err_no=data.get("err_no", 0),
            err_msg=data.get("err_msg", ""),
            draft_id=payload.get("id", ""),
            article_id=payload.get("article_id", ""),
        )


@dataclass
class PublishArticleResponse(ApiResponse):
    """发布文章响应"""
    article_id: str = ""
    link: str = ""
    
    @classmethod
    def from_dict(cls, data: dict, article_link_template: str = "https://juejin.cn/post/%s") -> "PublishArticleResponse":
        article_id = _data_dict(data).get("article_id", "")
        return cls(
            err_no=data.get("err_no", 0),
            err_msg=data.get("err_msg", ""),
            article_id=article_id,
            link=article_link_template % article_id if article_id else "",
        )


@dataclass
class DraftItem:
    """草稿项"""
    id: str
    title: str
    content: str = ""
    brief_content: str = ""
    category_id: str = ""
    tag_ids: list[str] = field(default_factory=list)
    ctime: str = ""
    mtime: str = ""
    status: int = 0


@dataclass
class ListDraftsResponse(ApiResponse):
    """草稿列表响应"""
    drafts: list[DraftItem] = field(default_factory=list)
    total: int = 0
    
    @classmethod
    def from_dict(cls, data: dict) -> "ListDraftsResponse":
        drafts = []
        for item in _data_list(data):
            if not isinstance(item, dict):
                continue
            drafts.append(DraftItem(
                id=item.get("id", ""),
                title=item.get("title", ""),
                content=item.get("mark_content", ""),
                brief_content=item.get("brief_content", ""),
                category_id=item.get("category_id", ""),
                tag_ids=item.get("tag_ids", []),
                ctime=item.get("ctime", ""),
                mtime=item.get("mtime", ""),
                status=item.get("status", 0),
            ))
        return cls(
            err_no=data.get("err_no", 0),
            err_msg=data.get("err_msg", ""),
            drafts=drafts,
            total=_total(data),
        )


@dataclass
class ArticleItem:
    """文章项"""
    article_id: str
    title: str
    content: str = ""
    brief_content: str = ""
    category_id: str = ""
    tag_ids: list[str] = field(default_factory=list)
    view_count: int = 0
    digg_count: int = 0
    comment_count: int = 0
    collect_count: int = 0
    ctime: str = ""
    rtime: str = ""
    status: int = 0
    audit_status: int = 0
    cover_image: str = ""


@dataclass
class ListArticlesResponse(ApiResponse):
    """文章列表响应"""
    articles: list[ArticleItem] = field(default_factory=list)
    total: int = 0
    has_more: bool = False
    
    @classmethod
    def from_dict(cls, data: dict) -> "ListArticlesResponse":
        articles = []
        for item in _data_list(data):
            if not isinstance(item, dict):
                continue
            articles.append(ArticleItem(
                article_id=str(item.get("article_id", "")),
                title=item.get("title", ""),
                content=item.get("mark_content", ""),
                brief_content=item.get("brief_content", ""),
                category_id=item.get("category_id", ""),
                tag_ids=item.get("tag_ids", []),
                view_count=item.get("view_count", 0),
                digg_count=item.get("digg_count", 0),
                comment_count=item.get("comment_count", 0),
                collect_count=item.get("collect_count", 0),
                ctime=item.get("ctime", ""),
                rtime=item.get("rtime", ""),
                status=item.get("status", 0),
                audit_status=item.get("audit_status", 0),
                cover_image=item.get("cover_image", ""),
            ))
        return cls(
            err_no=data.get("err_no", 0),
            err_msg=data.get("err_msg", ""),
            articles=articles,
            total=_total(data),
            has_more=bool(_data_dict(data).get("has_more", False)),
        )


@dataclass
class CategoryItem:
    """分类项"""
    category_id: str
    category_name: str
    category_url: str = ""


@dataclass
class ListCategoriesResponse(ApiResponse):
    """分类列表响应"""
    categories: list[CategoryItem] = field(default_factory=list)
    
    @classmethod
    def from_dict(cls, data: dict) -> "ListCategoriesResponse":
        categories = []
        for item in _data_list(data):
            if not isinstance(item, dict):
                continue
            # 真实结构是 data[].category.category_name，扁平结构则直接就是自身
            cat = item.get("category")
            if not isinstance(cat, dict):
                cat = item
            categories.append(CategoryItem(
                category_id=cat.get("category_id", ""),
                category_name=cat.get("category_name", ""),
                category_url=cat.get("category_url", ""),
            ))
        return cls(
            err_no=data.get("err_no", 0),
            err_msg=data.get("err_msg", ""),
            categories=categories,
        )


@dataclass
class TagItem:
    """标签项"""
    tag_id: str
    tag_name: str
    tag_url: str = ""
    article_count: int = 0


@dataclass
class ListTagsResponse(ApiResponse):
    """标签列表响应"""
    tags: list[TagItem] = field(default_factory=list)
    
    @classmethod
    def from_dict(cls, data: dict) -> "ListTagsResponse":
        tags = []
        for item in _data_list(data):
            if not isinstance(item, dict):
                continue
            # 真实结构是 data[].tag.tag_name，扁平结构则直接就是自身
            tag = item.get("tag")
            if not isinstance(tag, dict):
                tag = item
            tags.append(TagItem(
                tag_id=tag.get("tag_id", ""),
                tag_name=tag.get("tag_name", ""),
                tag_url=tag.get("tag_url", ""),
                article_count=tag.get("post_article_count", tag.get("article_count", 0)),
            ))
        return cls(
            err_no=data.get("err_no", 0),
            err_msg=data.get("err_msg", ""),
            tags=tags,
        )


@dataclass
class UserInfo(ApiResponse):
    """用户信息"""
    user_id: str = ""
    user_name: str = ""
    avatar_url: str = ""
    company: str = ""
    job_title: str = ""
    level: int = 0
    article_count: int = 0
    digg_count: int = 0
    follower_count: int = 0
    can_tag_cnt: int = 0

    @classmethod
    def from_dict(cls, data: dict) -> "UserInfo":
        u = _data_dict(data)
        return cls(
            err_no=data.get("err_no", 0),
            err_msg=data.get("err_msg", ""),
            user_id=str(u.get("user_id", "")),
            user_name=u.get("user_name", ""),
            avatar_url=u.get("avatar_large", u.get("avatar_url", "")),
            company=u.get("company", ""),
            job_title=u.get("job_title", ""),
            level=u.get("level", 0),
            article_count=u.get("post_article_count", u.get("article_count", 0)),
            digg_count=u.get("got_digg_count", u.get("digg_count", 0)),
            follower_count=u.get("follower_count", 0),
            # 该账号每篇文章允许的最大标签数，本账号为 1
            can_tag_cnt=u.get("can_tag_cnt", 0),
        )
