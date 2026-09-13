# 掘金 MCP 服务器 - API 测试结论

## 日期
2026-04-02

## 测试环境
- Cookie: sessionid=dc673cde72c7c81539d2fa39e65f532e
- 测试工具: Python + urllib

## 核心结论

### 1. 认证方式
**只需要 `sessionid`，不需要完整的 Cookie！**

```bash
# 正确的环境变量设置
export JUEJIN_COOKIE="sessionid=你的sessionid"

# 不需要以下参数：
# - ❌ 完整的 Cookie（包含多个字段）
# - ❌ aid 参数
# - ❌ uuid 参数
```

### 2. 各接口认证要求

| 接口 | URL | 必需认证 | 备注 |
|------|-----|----------|------|
| 文章列表 | `content_api/v1/article/list_by_user` | sessionid | 不需要 aid/uuid |
| 草稿列表 | `content_api/v1/article_draft/list_by_user` | sessionid | 注意是 `list_by_user` 不是 `list` |
| 草稿详情 | `content_api/v1/article_draft/detail` | sessionid | 参数用 `draft_id` |
| 分类列表 | `tag_api/v1/query_category_list` | sessionid | 无需其他参数 |
| 标签列表 | `tag_api/v1/query_tag_list` | sessionid | 参数用 `cursor`+`limit` 不是 `page_no` |
| 创建草稿 | `content_api/v1/article_draft/create` | sessionid | 需要 `category_id` 和 `tag_ids` |
| 更新草稿 | `content_api/v1/article_draft/update` | sessionid | 参数用 `id` 不是 `draft_id` |
| 发布文章 | `content_api/v1/article/publish` | sessionid + 字数参数 | **见下方** |
| 删除草稿 | `content_api/v1/article_draft/delete` | sessionid | 参数用 `draft_id` 不是 `id` |
| 删除文章 | `content_api/v1/article/delete` | sessionid | 参数用 `article_id` |

### 3. 发布文章的真实要求（2026-09-13 用浏览器逐字核对）

**必需：摘要（`brief_content`）≤ 100 字。**

超过时 `article/publish` 返回 `err_no=2「参数错误」`，而 `article_draft/create` /
`article_draft/update` **不校验**（照样返回 success），所以坑一直藏到发布那一步才炸。
实测：摘要 97 字、112 字发布成功；172 字必然失败（硬上限落在 113~172 字之间）。
创作者中心的摘要输入框标的就是「/100」——写草稿时就把摘要压到 100 字以内。

**旧文档在这一节写错了**，订正如下：

| 参数 | 旧文档说法 | 实测结论 |
|---|---|---|
| `encrypted_word_count` | 必需，要从 DevTools 复制 | **非必需**，完全不传也能发布成功 |
| `origin_word_count` | 必需，「正文实际字数」 | 非必需。它是创作者中心底部的「**正文字数**」（实测 2386），不是 `len(正文)` 字符数（5496） |

创作者中心点「发布」时实际发出的请求（DevTools 抓包，一字未改）：

```
POST https://api.juejin.cn/content_api/v1/article/publish?aid=2608&uuid=<客户端生成>
x-secsdk-csrf-token: 000100000001c3c8...   # 浏览器会带；脚本不带也能成功
Cookie: sessionid=...
{"draft_id":"7684534717442310154","sync_to_org":false,"column_ids":[],"theme_ids":[],
 "encrypted_word_count":1075626,"origin_word_count":2386}
```

排查提示：发布报 `参数错误` 时**先量摘要长度**，再去看浏览器真实请求；
不要从 cookie / uuid / csrf 入手——这三项实测都不是发布成功的必要条件。

### 4. 各接口请求参数说明

#### 标签列表
```json
{
  "cursor": "20",      // 分页游标，不是 page_no
  "key_word": "",      // 搜索关键词
  "limit": 10,         // 每页数量，不是 page_size
  "sort_type": 1       // 排序类型
}
```

#### 创建草稿
```json
{
  "title": "文章标题",
  "mark_content": "正文内容（Markdown）",
  "brief_content": "摘要",
  "category_id": "6809637769959178254",  // 必需！分类ID
  "tag_ids": ["6809640408797167623"],     // 必需！标签ID数组
  "edit_type": 10,
  "html_content": "deprecated"
}
```

#### 草稿详情
```json
{
  "draft_id": "草稿ID"
}
```
**备注：草稿详情接口也可用于查询已发布文章的内容**

#### 更新草稿
```json
{
  "id": "草稿ID",      // 注意：用 id 不是 draft_id
  "title": "新标题",
  "mark_content": "新内容",
  "brief_content": "新摘要",
  "category_id": "6809637769959178254",
  "tag_ids": ["6809640408797167623"],
  "edit_type": 10,
  "html_content": "deprecated"
}
```

#### 删除草稿
```json
{
  "draft_id": "草稿ID"  // 注意：用 draft_id 不是 id
}
```

#### 删除文章
```json
{
  "article_id": "文章ID"
}
```

### 5. 常见错误

| 错误 | 原因 | 解决 |
|------|------|------|
| "请求路由不存在" | 使用了错误的 URL | 草稿列表用 `list_by_user` 不是 `list` |
| "参数错误" | 多半是**摘要（`brief_content`）超过 100 字**（create/update 不校验，只有 publish 拦）；也可能是端点或参数名写错 | 把摘要压到 ≤100 字；再核对端点、参数名。别急着怀疑 cookie/uuid/csrf |
| 返回空数据 | Cookie 无效或过期 | 重新从浏览器获取 sessionid |

### 6. 参考 cURL 命令

```bash
# 文章列表
curl 'https://api.juejin.cn/content_api/v1/article/list_by_user' \
  -H 'Cookie: sessionid=xxx' \
  -H 'Content-Type: application/json' \
  --data '{"page_no":1,"page_size":10}'

# 草稿列表（注意是 list_by_user）
curl 'https://api.juejin.cn/content_api/v1/article_draft/list_by_user' \
  -H 'Cookie: sessionid=xxx' \
  -H 'Content-Type: application/json' \
  --data '{"keyword":"","page_no":1,"page_size":10}'

# 草稿详情
curl 'https://api.juejin.cn/content_api/v1/article_draft/detail' \
  -H 'Cookie: sessionid=xxx' \
  -H 'Content-Type: application/json' \
  --data '{"draft_id":"xxx"}'

# 分类列表
curl 'https://api.juejin.cn/tag_api/v1/query_category_list' \
  -H 'Cookie: sessionid=xxx' \
  -H 'Content-Type: application/json' \
  --data '{}'

# 标签列表（注意参数不同）
curl 'https://api.juejin.cn/tag_api/v1/query_tag_list' \
  -H 'Cookie: sessionid=xxx' \
  -H 'Content-Type: application/json' \
  --data '{"cursor":"20","key_word":"","limit":10,"sort_type":1}'

# 创建草稿（需要分类和标签）
curl 'https://api.juejin.cn/content_api/v1/article_draft/create' \
  -H 'Cookie: sessionid=xxx' \
  -H 'Content-Type: application/json' \
  --data '{"title":"标题","mark_content":"内容","brief_content":"摘要","category_id":"6809637769959178254","tag_ids":["6809640408797167623"],"edit_type":10,"html_content":"deprecated"}'

# 更新草稿（注意用 id 不是 draft_id）
curl 'https://api.juejin.cn/content_api/v1/article_draft/update' \
  -H 'Cookie: sessionid=xxx' \
  -H 'Content-Type: application/json' \
  --data '{"id":"草稿ID","title":"新标题","mark_content":"新内容","brief_content":"新摘要","category_id":"6809637769959178254","tag_ids":["6809640408797167623"],"edit_type":10,"html_content":"deprecated"}'

# 发布文章（需要字数参数）
curl 'https://api.juejin.cn/content_api/v1/article/publish' \
  -H 'Cookie: sessionid=xxx' \
  -H 'Content-Type: application/json' \
  --data '{"draft_id":"xxx","sync_to_org":false,"column_ids":[],"theme_ids":[],"encrypted_word_count":1077871,"origin_word_count":15}'

# 删除草稿（注意用 draft_id 不是 id）
curl 'https://api.juejin.cn/content_api/v1/article_draft/delete' \
  -H 'Cookie: sessionid=xxx' \
  -H 'Content-Type: application/json' \
  --data '{"draft_id":"xxx"}'

# 删除文章
curl 'https://api.juejin.cn/content_api/v1/article/delete' \
  -H 'Cookie: sessionid=xxx' \
  -H 'Content-Type: application/json' \
  --data '{"article_id":"xxx"}'
```

## 代码修改建议

1. **简化配置**: 移除 `aid` 和 `uuid` 配置项
2. **修正 URL**: 草稿列表使用 `list_by_user`
3. **发布接口**: 确保传入 `encrypted_word_count` 和 `origin_word_count`
