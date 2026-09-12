"""
请求数据模型
"""

from dataclasses import dataclass, field
from typing import Optional


@dataclass
class CreateDraftRequest:
    """创建草稿请求"""
    title: str
    content: str
    description: Optional[str] = None
    category_id: Optional[str] = None
    tag_ids: list[str] = field(default_factory=list)
    cover_image: Optional[str] = None
    edit_type: int = 10
    
    def to_api_dict(self) -> dict:
        """转换为 API 请求格式"""
        return {
            "title": self.title,
            "mark_content": self.content,
            "brief_content": self.description or "",
            "category_id": self.category_id or "",
            "tag_ids": self.tag_ids or [],
            "cover_image": self.cover_image or "",
            "edit_type": self.edit_type,
            "html_content": "deprecated",
        }


@dataclass
class UpdateDraftRequest:
    """更新草稿请求（与创作者中心 article_draft/update 请求体一致，字段为蛇形命名）"""
    draft_id: str
    title: Optional[str] = None
    content: Optional[str] = None
    description: Optional[str] = None
    category_id: Optional[str] = None
    tag_ids: Optional[list[str]] = None
    link_url: Optional[str] = None
    cover_image: Optional[str] = None
    is_gfw: Optional[int] = None
    is_english: Optional[int] = None
    is_original: Optional[int] = None
    edit_type: Optional[int] = None
    theme_ids: Optional[list[str]] = None
    pics: Optional[list[str]] = None

    def to_api_dict(self) -> dict:
        """转换为 API 请求体：仅包含调用方显式传入的字段 + 必填 id。"""
        result: dict = {"id": self.draft_id}
        if self.title is not None:
            result["title"] = self.title
        if self.content is not None:
            result["mark_content"] = self.content
        if self.description is not None:
            result["brief_content"] = self.description
        if self.category_id is not None:
            result["category_id"] = self.category_id
        if self.tag_ids is not None:
            result["tag_ids"] = self.tag_ids
        if self.link_url is not None:
            result["link_url"] = self.link_url
        if self.cover_image is not None:
            result["cover_image"] = self.cover_image
        if self.is_gfw is not None:
            result["is_gfw"] = self.is_gfw
        if self.is_english is not None:
            result["is_english"] = self.is_english
        if self.is_original is not None:
            result["is_original"] = self.is_original
        if self.edit_type is not None:
            result["edit_type"] = self.edit_type
        if self.theme_ids is not None:
            result["theme_ids"] = self.theme_ids
        if self.pics is not None:
            result["pics"] = self.pics
        # 与网页一致：有正文时带 html_content 占位
        if self.content is not None:
            result["html_content"] = "deprecated"
        return result


@dataclass
class PublishArticleRequest:
    """发布文章请求（article/publish，可与更新草稿链式调用实现「更新并发布」）"""
    draft_id: str
    sync_to_org: bool = False
    column_ids: list[str] = field(default_factory=list)
    theme_ids: list[str] = field(default_factory=list)
    encrypted_word_count: Optional[int] = None
    origin_word_count: Optional[int] = None

    def to_api_dict(self) -> dict:
        """转换为 API 请求格式"""
        out = {
            "draft_id": self.draft_id,
            "sync_to_org": self.sync_to_org,
            "column_ids": self.column_ids or [],
            "theme_ids": self.theme_ids or [],
        }
        if self.encrypted_word_count is not None:
            out["encrypted_word_count"] = self.encrypted_word_count
        if self.origin_word_count is not None:
            out["origin_word_count"] = self.origin_word_count
        return out


@dataclass
class ListDraftsRequest:
    """获取草稿列表请求"""
    page: int = 1
    page_size: int = 10
    keyword: Optional[str] = None

    def to_api_dict(self) -> dict:
        return {
            "page_no": self.page,
            "page_size": self.page_size,
            "keyword": self.keyword or "",
        }


@dataclass
class ListArticlesRequest:
    """获取文章列表请求"""
    page: int = 1
    page_size: int = 10
    keyword: Optional[str] = None
    audit_status: Optional[int] = None
    
    def to_api_dict(self) -> dict:
        return {
            "page_no": self.page,
            "page_size": self.page_size,
            "keyword": self.keyword or "",
            "audit_status": self.audit_status,
        }


@dataclass
class ListTagsRequest:
    """获取标签列表请求

    接口参数是 cursor/limit/sort_type，其中 cursor 是偏移量而非页码。
    """
    keyword: Optional[str] = None
    page: int = 1
    page_size: int = 20
    sort_type: int = 1

    def to_api_dict(self) -> dict:
        return {
            "cursor": str((max(self.page, 1) - 1) * self.page_size),
            "limit": self.page_size,
            "key_word": self.keyword or "",
            "sort_type": self.sort_type,
        }
