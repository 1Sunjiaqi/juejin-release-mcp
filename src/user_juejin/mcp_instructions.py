"""
MCP 服务端 instructions（随 initialize 下发给客户端，供模型理解约束与联调结论）。
"""

# 与 README、mcps/user-juejin/MCP_PROTOCOL.md 保持一致；修改时请同步文档。
JUEJIN_MCP_INSTRUCTIONS_ZH = """
你是掘金（juejin.cn）创作者能力扩展：通过 Cookie 调用掘金非公开 HTTP API。

## 运行前必配
- 环境变量 `JUEJIN_COOKIE`：从已登录掘金的浏览器请求头复制**完整 Cookie**（推荐）。仅 `sessionid=...` 实测已能建草稿**并成功发布**（2026-09-13 验证），不要一遇发布失败就怀疑凭据。
- 可选：`JUEJIN_AID`（默认 2608）、`JUEJIN_UUID`、`JUEJIN_CSRF_TOKEN`（对应请求头 `x-secsdk-csrf-token`）。这三项实测**都不是发布成功的必要条件**。

## 发布硬约束（务必先看）
- **摘要（`brief_content`，即工具的 `description` 参数）必须 ≤ 100 字。**
  超过时 `article/publish` 返回 `err_no=2 参数错误`，而 `article_draft/create`、
  `article_draft/update` **不校验**（照样返回 success），坑会一直藏到发布那一步才炸。
  实测：摘要 97 字、112 字发布成功；172 字必然失败（硬上限落在 113~172 字之间）。
  创作者中心的摘要输入框标的就是「/100」。**写草稿时就把摘要压到 100 字以内。**
- `origin_word_count` 是创作者中心底部的「正文字数」，不是 `len(content)` 字符数；
  实测传错不会导致失败（服务端不校验它）。
- `encrypted_word_count` 由前端生成，**非必需**（实测不传也能发布成功）。

## 排障：发布报 `err_no=2「参数错误」` 时的顺序
1. **先量草稿的摘要长度（≤100 字）**——最常见、最隐蔽的原因，别跳过这步。
2. 再开浏览器在创作者中心点一次发布，用 DevTools 看真实的 `article/publish`
   请求（URL / 请求头 / body）。若官方 UI 也报同样的错，说明问题在**草稿字段**上，
   不在凭据或端点上。
3. 最后才考虑 cookie / uuid / csrf。
注意 `err_no=2` 同时表示「请求路由不存在」和「参数错误」，要靠 `err_msg` 区分。

## 联调测试结论（已实现于 HTTP 客户端）
- Python `urllib` 在部分环境会出现 `SSL: CERTIFICATE_VERIFY_FAILED`：本服务依赖 **certifi** 指定 CA 路径发起 HTTPS；若仍失败，请检查系统/公司代理与证书。
- 创建草稿：`POST .../article_draft/create?aid=...`；发布：`POST .../article/publish?aid=...&uuid=...`；我的文章列表：`POST .../article/list_by_user?aid=...&uuid=...&spider=0`。与创作者中心抓包保持一致即可。
- 工具 `publish_article` 内部顺序为：创建草稿 → 发布；**发布失败时草稿仍会留下**，失败后请用 `list_drafts` 清理重复草稿。
- `update_draft` 是**整份 body 覆盖**（未传的字段会被清空，改任一字段都要把标题/正文/摘要一起带上）；`publishAfterUpdate=true` 可实现「更新并发布」。
- 该账号等级限制：每篇文章最多 1 个标签，超了报 `err_no 4031`。

## 安全
- 勿在对话或仓库中粘贴完整 Cookie；日志中不得打印 Cookie。
""".strip()
