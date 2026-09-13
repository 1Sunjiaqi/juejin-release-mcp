"""
掘金 MCP 服务器入口
"""

import asyncio
import json
import logging
import sys
from typing import Any

from mcp.server import Server
from mcp.server.stdio import stdio_server
from mcp.types import Tool, TextContent

from .config import JuejinConfig
from .clients.juejin_client import JuejinClient
from .mcp_instructions import JUEJIN_MCP_INSTRUCTIONS_ZH
from .services.article_service import ArticleService
from . import __version__

# 配置日志
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    stream=sys.stderr,
)
logger = logging.getLogger(__name__)

# 创建服务器实例（instructions 随 MCP initialize 下发，见 mcp_instructions.py）
server = Server(
    "juejin-mcp",
    version=__version__,
    instructions=JUEJIN_MCP_INSTRUCTIONS_ZH,
)

# 全局客户端
_client: JuejinClient = None
_article_service: ArticleService = None


def get_client() -> JuejinClient:
    """获取掘金客户端"""
    global _client
    if _client is None:
        config = JuejinConfig.from_env()
        _client = JuejinClient(config)
    return _client


def get_article_service() -> ArticleService:
    """获取文章服务"""
    global _article_service
    if _article_service is None:
        _article_service = ArticleService(get_client())
    return _article_service


def _json_result(data: Any) -> str:
    """将结果转换为 JSON 字符串"""
    if isinstance(data, dict):
        return json.dumps(data, ensure_ascii=False, indent=2)
    return str(data)


# ==================== 工具定义 ====================

@server.list_tools()
async def list_tools() -> list[Tool]:
    """列出所有可用工具"""
    return [
        Tool(
            name="publish_article",
            description=(
                "发布文章到掘金平台。自动完成创建草稿和发布两步操作。需要配置 JUEJIN_COOKIE 环境变量。"
                "注意：摘要（description）必须 ≤100 字，否则 article/publish 返回 err_no=2「参数错误」"
                "（而 create/update 不校验，只有发布这步会拦）；发布失败时草稿仍会留在草稿箱，请用 list_drafts 清理。"
            ),
            inputSchema={
                "type": "object",
                "properties": {
                    "title": {"type": "string", "description": "文章标题，必填"},
                    "content": {"type": "string", "description": "文章正文，Markdown 格式，必填"},
                    "description": {"type": "string", "description": "文章摘要，可选。为空时自动从正文提取。必须 ≤100 字，否则发布被拒"},
                    "categoryId": {"type": "string", "description": "分类 ID，可选"},
                    "tagIds": {"type": "array", "items": {"type": "string"}, "description": "标签 ID 列表，可选"},
                },
                "required": ["title", "content"],
            },
        ),
        Tool(
            name="create_draft",
            description="创建掘金文章草稿。仅创建草稿不发布，返回草稿 ID。",
            inputSchema={
                "type": "object",
                "properties": {
                    "title": {"type": "string", "description": "文章标题，必填"},
                    "content": {"type": "string", "description": "文章正文，Markdown 格式，必填"},
                    "description": {"type": "string", "description": "文章摘要，可选。必须 ≤100 字，否则发布被拒（create/update 不校验，只有 publish 拦）"},
                    "categoryId": {"type": "string", "description": "分类 ID，可选"},
                    "tagIds": {"type": "array", "items": {"type": "string"}, "description": "标签 ID 列表，可选"},
                    "coverImage": {"type": "string", "description": "封面图片 URL，可选"},
                },
                "required": ["title", "content"],
            },
        ),
        Tool(
            name="update_draft",
            description=(
                "更新掘金文章草稿（对应 content_api/v1/article_draft/update?aid=&uuid=）。"
                "创作者中心在「保存修改后发布」时为先 update 再 publish；"
                "可将 publishAfterUpdate 设为 true，在同一次调用内先更新草稿再调用发布接口。"
            ),
            inputSchema={
                "type": "object",
                "properties": {
                    "draftId": {"type": "string", "description": "草稿 ID（请求体字段 id），必填"},
                    "title": {"type": "string", "description": "文章标题，可选"},
                    "content": {"type": "string", "description": "文章正文 Markdown（mark_content），可选"},
                    "description": {"type": "string", "description": "摘要（brief_content），可选。必须 ≤100 字，否则后续发布被拒"},
                    "categoryId": {"type": "string", "description": "分类 ID（category_id），可选"},
                    "tagIds": {"type": "array", "items": {"type": "string"}, "description": "标签 ID 列表（tag_ids），可选"},
                    "linkUrl": {"type": "string", "description": "link_url，可选，默认不传则不写入"},
                    "coverImage": {"type": "string", "description": "封面 cover_image，可选"},
                    "isGfw": {"type": "integer", "description": "is_gfw，可选"},
                    "isEnglish": {"type": "integer", "description": "is_english，可选"},
                    "isOriginal": {"type": "integer", "description": "is_original，可选"},
                    "editType": {"type": "integer", "description": "edit_type，默认网页为 10，可选"},
                    "themeIds": {"type": "array", "items": {"type": "string"}, "description": "theme_ids，可选"},
                    "pics": {"type": "array", "items": {"type": "string"}, "description": "pics，可选"},
                    "publishAfterUpdate": {
                        "type": "boolean",
                        "description": "为 true 时在更新成功后调用 article/publish（更新并发布）",
                    },
                    "encryptedWordCount": {
                        "type": "integer",
                        "description": "发布请求 encrypted_word_count，可选；与网页一致时可从开发者工具复制",
                    },
                    "originWordCount": {
                        "type": "integer",
                        "description": "发布请求 origin_word_count，可选；未传且提供了 content 时用正文长度估算",
                    },
                },
                "required": ["draftId"],
            },
        ),
        Tool(
            name="delete_draft",
            description="删除掘金文章草稿。根据草稿 ID 删除草稿。",
            inputSchema={
                "type": "object",
                "properties": {
                    "draftId": {"type": "string", "description": "草稿 ID，必填"},
                },
                "required": ["draftId"],
            },
        ),
        Tool(
            name="list_drafts",
            description="获取掘金文章草稿列表。分页查询当前用户的草稿。",
            inputSchema={
                "type": "object",
                "properties": {
                    "page": {"type": "integer", "description": "页码，从 1 开始，默认 1"},
                    "pageSize": {"type": "integer", "description": "每页数量，默认 10"},
                },
            },
        ),
        Tool(
            name="get_article",
            description="获取掘金文章详情。根据文章 ID 获取文章内容。",
            inputSchema={
                "type": "object",
                "properties": {
                    "articleId": {"type": "string", "description": "文章 ID，必填"},
                },
                "required": ["articleId"],
            },
        ),
        Tool(
            name="list_articles",
            description=(
                "获取当前用户的文章列表（article/list_by_user?aid=&uuid=&spider=0）。"
                "支持 keyword、audit_status 等与网页一致的查询参数。"
            ),
            inputSchema={
                "type": "object",
                "properties": {
                    "page": {"type": "integer", "description": "页码 page_no，从 1 开始，默认 1"},
                    "pageSize": {"type": "integer", "description": "每页 page_size，默认 10"},
                    "keyword": {"type": "string", "description": "搜索关键词，可选"},
                    "auditStatus": {
                        "type": "integer",
                        "description": "审核状态 audit_status，可选；可与网页抓包一致传 null（不传则请求体中为 null）",
                    },
                },
            },
        ),
        Tool(
            name="update_article",
            description="更新已发布的掘金文章。根据文章 ID 更新文章内容。",
            inputSchema={
                "type": "object",
                "properties": {
                    "articleId": {"type": "string", "description": "文章 ID，必填"},
                    "title": {"type": "string", "description": "文章标题，可选"},
                    "content": {"type": "string", "description": "文章正文，可选"},
                    "description": {"type": "string", "description": "文章摘要，可选。必须 ≤100 字，否则发布被拒（create/update 不校验，只有 publish 拦）"},
                    "categoryId": {"type": "string", "description": "分类 ID，可选"},
                    "tagIds": {"type": "array", "items": {"type": "string"}, "description": "标签 ID 列表，可选"},
                },
                "required": ["articleId"],
            },
        ),
        Tool(
            name="delete_article",
            description="删除已发布的掘金文章。根据文章 ID 删除文章，操作不可恢复。",
            inputSchema={
                "type": "object",
                "properties": {
                    "articleId": {"type": "string", "description": "文章 ID，必填"},
                },
                "required": ["articleId"],
            },
        ),
        Tool(
            name="list_categories",
            description="获取掘金文章分类列表。返回所有可用的文章分类。",
            inputSchema={"type": "object", "properties": {}},
        ),
        Tool(
            name="list_tags",
            description="获取掘金文章标签列表。返回热门标签或根据关键词搜索标签。",
            inputSchema={
                "type": "object",
                "properties": {
                    "keyword": {"type": "string", "description": "搜索关键词，可选"},
                    "page": {"type": "integer", "description": "页码，默认 1"},
                    "pageSize": {"type": "integer", "description": "每页数量，默认 20"},
                },
            },
        ),
        Tool(
            name="get_user_info",
            description="获取当前登录用户信息。用于验证 Cookie 是否有效。",
            inputSchema={"type": "object", "properties": {}},
        ),
    ]


@server.call_tool()
async def call_tool(name: str, arguments: dict) -> list[TextContent]:
    """执行工具调用"""
    try:
        client = get_client()
        article_service = get_article_service()
        
        if name == "publish_article":
            result = article_service.publish_article(
                title=arguments["title"],
                content=arguments["content"],
                description=arguments.get("description"),
                category_id=arguments.get("categoryId"),
                tag_ids=arguments.get("tagIds"),
            )
            return [TextContent(type="text", text=_json_result(result))]
        
        elif name == "create_draft":
            result = article_service.create_draft(
                title=arguments["title"],
                content=arguments["content"],
                description=arguments.get("description"),
                category_id=arguments.get("categoryId"),
                tag_ids=arguments.get("tagIds"),
                cover_image=arguments.get("coverImage"),
            )
            return [TextContent(type="text", text=_json_result(result))]
        
        elif name == "update_draft":
            from .models.request import PublishArticleRequest, UpdateDraftRequest

            req = UpdateDraftRequest(
                draft_id=arguments["draftId"],
                title=arguments.get("title"),
                content=arguments.get("content"),
                description=arguments.get("description"),
                category_id=arguments.get("categoryId"),
                tag_ids=arguments.get("tagIds"),
                link_url=arguments.get("linkUrl"),
                cover_image=arguments.get("coverImage"),
                is_gfw=arguments.get("isGfw"),
                is_english=arguments.get("isEnglish"),
                is_original=arguments.get("isOriginal"),
                edit_type=arguments.get("editType"),
                theme_ids=arguments.get("themeIds"),
                pics=arguments.get("pics"),
            )
            resp = client.update_draft(req)
            result: dict = {
                "success": resp.success,
                "draft_id": resp.draft_id or arguments["draftId"],
                "error": resp.err_msg if not resp.success else None,
            }
            if resp.success and arguments.get("publishAfterUpdate"):
                pub = PublishArticleRequest(
                    draft_id=arguments["draftId"],
                    sync_to_org=False,
                    column_ids=[],
                    theme_ids=[],
                    encrypted_word_count=arguments.get("encryptedWordCount"),
                    origin_word_count=arguments.get("originWordCount")
                    if arguments.get("originWordCount") is not None
                    else (len(arguments["content"]) if arguments.get("content") else None),
                )
                pub_resp = client.publish_article(pub)
                result["publish"] = {
                    "success": pub_resp.success,
                    "article_id": pub_resp.article_id,
                    "link": pub_resp.link,
                    "error": pub_resp.err_msg if not pub_resp.success else None,
                }
            return [TextContent(type="text", text=_json_result(result))]
        
        elif name == "delete_draft":
            result = client.delete_draft(arguments["draftId"])
            return [TextContent(type="text", text=_json_result(result))]
        
        elif name == "list_drafts":
            from .models.request import ListDraftsRequest
            req = ListDraftsRequest(
                page=arguments.get("page", 1),
                page_size=arguments.get("pageSize", 10),
            )
            resp = client.list_drafts(req)
            result = {
                "success": resp.success,
                "total": resp.total,
                "drafts": [
                    {
                        "id": d.id,
                        "title": d.title,
                        "brief_content": d.brief_content,
                        "category_id": d.category_id,
                        "tag_ids": d.tag_ids,
                        "ctime": d.ctime,
                        "mtime": d.mtime,
                    }
                    for d in resp.drafts
                ],
            }
            return [TextContent(type="text", text=_json_result(result))]
        
        elif name == "get_article":
            result = client.get_article(arguments["articleId"])
            return [TextContent(type="text", text=_json_result(result))]
        
        elif name == "list_articles":
            from .models.request import ListArticlesRequest
            req = ListArticlesRequest(
                page=arguments.get("page", 1),
                page_size=arguments.get("pageSize", 10),
                keyword=arguments.get("keyword"),
                audit_status=arguments.get("auditStatus"),
            )
            resp = client.list_articles(req)
            result = {
                "success": resp.success,
                "total": resp.total,
                "has_more": getattr(resp, "has_more", False),
                "articles": [
                    {
                        "article_id": a.article_id,
                        "title": a.title,
                        "brief_content": a.brief_content,
                        "view_count": a.view_count,
                        "digg_count": a.digg_count,
                        "comment_count": a.comment_count,
                        "ctime": a.ctime,
                    }
                    for a in resp.articles
                ],
            }
            return [TextContent(type="text", text=_json_result(result))]
        
        elif name == "update_article":
            result = client.update_article(
                arguments["articleId"],
                title=arguments.get("title"),
                mark_content=arguments.get("content"),
                brief_content=arguments.get("description"),
                category_id=arguments.get("categoryId"),
                tag_ids=arguments.get("tagIds"),
            )
            return [TextContent(type="text", text=_json_result(result))]
        
        elif name == "delete_article":
            result = client.delete_article(arguments["articleId"])
            return [TextContent(type="text", text=_json_result(result))]
        
        elif name == "list_categories":
            resp = client.list_categories()
            result = {
                "success": resp.success,
                "categories": [
                    {"id": c.category_id, "name": c.category_name}
                    for c in resp.categories
                ],
            }
            return [TextContent(type="text", text=_json_result(result))]
        
        elif name == "list_tags":
            from .models.request import ListTagsRequest
            req = ListTagsRequest(
                keyword=arguments.get("keyword"),
                page=arguments.get("page", 1),
                page_size=arguments.get("pageSize", 20),
            )
            resp = client.list_tags(req)
            result = {
                "success": resp.success,
                "tags": [
                    {"id": t.tag_id, "name": t.tag_name, "article_count": t.article_count}
                    for t in resp.tags
                ],
            }
            return [TextContent(type="text", text=_json_result(result))]
        
        elif name == "get_user_info":
            resp = client.get_user_info()
            result = {
                "success": resp.success,
                "user_id": resp.user_id,
                "user_name": resp.user_name,
                "avatar_url": resp.avatar_url,
                "company": resp.company,
                "job_title": resp.job_title,
                "level": resp.level,
                "article_count": resp.article_count,
                "follower_count": resp.follower_count,
                "can_tag_cnt": resp.can_tag_cnt,
            }
            return [TextContent(type="text", text=_json_result(result))]
        
        else:
            return [TextContent(type="text", text=f"未知工具: {name}")]
    
    except Exception as e:
        logger.exception(f"工具执行失败: {name}")
        return [TextContent(type="text", text=_json_result({"success": False, "error": str(e)}))]


async def run_server():
    """运行 MCP 服务器"""
    async with stdio_server() as (read_stream, write_stream):
        await server.run(read_stream, write_stream, server.create_initialization_options())


def main():
    """主入口"""
    asyncio.run(run_server())


if __name__ == "__main__":
    main()
