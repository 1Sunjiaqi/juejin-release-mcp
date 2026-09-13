"""
文章服务
提供文章发布、草稿管理等高级功能
"""

import logging
from typing import Optional

from ..clients.juejin_client import JuejinClient
from ..models.request import CreateDraftRequest, PublishArticleRequest
from ..models.response import CreateDraftResponse, PublishArticleResponse

logger = logging.getLogger(__name__)


class ArticleService:
    """文章服务"""
    
    def __init__(self, client: Optional[JuejinClient] = None):
        self.client = client or JuejinClient()
    
    def publish_article(
        self,
        title: str,
        content: str,
        description: Optional[str] = None,
        category_id: Optional[str] = None,
        tag_ids: Optional[list[str]] = None,
    ) -> dict:
        """
        发布文章（创建草稿 + 发布）
        
        Args:
            title: 文章标题
            content: 文章内容（Markdown）
            description: 文章摘要
            category_id: 分类ID
            tag_ids: 标签ID列表
            
        Returns:
            包含 article_id, link, draft_id 的字典
        """
        # 生成摘要
        if not description:
            description = self._generate_brief(content)
        
        # 1. 创建草稿
        draft_req = CreateDraftRequest(
            title=title,
            content=content,
            description=description,
            category_id=category_id,
            tag_ids=tag_ids or [],
        )
        draft_resp = self.client.create_draft(draft_req)
        
        if not draft_resp.success:
            return {
                "success": False,
                "error": draft_resp.err_msg,
                "code": draft_resp.err_no,
            }
        
        # 2. 发布文章
        publish_req = PublishArticleRequest(draft_id=draft_resp.draft_id)
        publish_resp = self.client.publish_article(publish_req)
        
        if not publish_resp.success:
            result = {
                "success": False,
                "error": publish_resp.err_msg,
                "code": publish_resp.err_no,
                "draft_id": draft_resp.draft_id,
                "brief_length": len(description),
            }
            if publish_resp.err_no == 2 and len(description) > 100:
                result["hint"] = (
                    f"摘要 {len(description)} 字，超过服务端上限（实测 112 字仍可发布、172 字必失败）。"
                    "publish 的「参数错误」多半就是这个；把摘要压到 ≤100 字后重发。"
                )
            return result
        
        return {
            "success": True,
            "article_id": publish_resp.article_id,
            "link": publish_resp.link,
            "draft_id": draft_resp.draft_id,
        }
    
    def create_draft(
        self,
        title: str,
        content: str,
        description: Optional[str] = None,
        category_id: Optional[str] = None,
        tag_ids: Optional[list[str]] = None,
        cover_image: Optional[str] = None,
    ) -> dict:
        """创建草稿"""
        if not description:
            description = self._generate_brief(content)
        
        req = CreateDraftRequest(
            title=title,
            content=content,
            description=description,
            category_id=category_id,
            tag_ids=tag_ids or [],
            cover_image=cover_image,
        )
        resp = self.client.create_draft(req)
        
        if not resp.success:
            return {
                "success": False,
                "error": resp.err_msg,
                "code": resp.err_no,
            }
        
        return {
            "success": True,
            "draft_id": resp.draft_id,
        }
    
    def _generate_brief(self, content: str, max_length: int = 100) -> str:
        """从内容生成摘要"""
        # 简单实现：移除 Markdown 标记后截取
        import re
        text = re.sub(r'[#*`_\[\]()>-]', '', content)
        text = re.sub(r'\n+', ' ', text)
        text = text.strip()
        if len(text) > max_length:
            text = text[:max_length]
        return text
