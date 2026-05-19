# 不开发 iOS 原生 App 的科研情报替代方案

## 1. 目标重述

原目标是做 iOS 原生 App，但现在更合理的目标是：

- 每天自动抓取科研论文和技术资讯。
- 来源包括 PubMed、bioRxiv、medRxiv、arXiv、RSS、指定网页或研究机构动态。
- 按神经科学、生物材料、AI、骨科等主题筛选。
- 生成中文精炼摘要、关键结论、方法亮点、价值判断和原文链接。
- 定时推送到手机端。
- 手机端不要求原生 App，只要查看方便、推送稳定、维护成本低。

核心判断：

> 这个需求本质上是“自动化内容流水线 + 移动端通知/阅读入口”，不是必须做 iOS App。

因此应优先选择：

- 无长期运行服务器，或尽量少服务器。
- 无 App Store、无 APNs 证书、无 Xcode 签名。
- 使用现成移动端 App 承担通知和阅读，例如飞书、企业微信、Telegram、邮件、Bark、Notion。
- 把后端抓取与摘要逻辑做成定时脚本或轻量 API。

---

## 2. 方案总览对比

| 方案 | 开发难度 | 部署复杂度 | 手机端体验 | 推送能力 | 扩展性 | 费用 | 稳定性 | 备案 | 适合个人吗 | 适合产品化吗 |
|---|---:|---:|---:|---:|---:|---:|---:|---|---|---|
| GitHub Actions + 飞书/企业微信机器人 + 邮件 + Markdown/HTML | 低 | 很低 | 好 | 好 | 中 | 低 | 中高 | 通常不需要 | 非常适合 | 中等 |
| GitHub Actions + Bark/ntfy + 静态页面 | 低 | 低 | iPhone 体验好 | 很好 | 中 | 低 | 中高 | 通常不需要 | 非常适合 | 较弱 |
| Telegram Bot + 静态页面/私聊消息 | 低 | 低 | 好 | 很好 | 中 | 低 | 高 | 不需要 | 适合可用 Telegram 的用户 | 中等 |
| 邮件 Newsletter | 很低 | 很低 | 中 | 中 | 中 | 低 | 高 | 不需要 | 非常适合 | 中等 |
| Notion 数据库 + 通知补充 | 低 | 低 | 好 | 弱到中 | 中 | 低到中 | 中 | 不需要 | 适合个人知识库 | 较弱 |
| Obsidian Sync/Markdown 仓库 | 中 | 低 | 中 | 弱 | 中 | 低到中 | 高 | 不需要 | 适合重度笔记用户 | 弱 |
| 静态网页/PWA + GitHub Pages/Cloudflare Pages | 中 | 低 | 好 | 中 | 中高 | 低 | 中 | 海外托管通常不需要 | 适合 | 中高 |
| FastAPI 后端 + Web/PWA 前端 | 中高 | 中 | 很好 | 中到高 | 高 | 中 | 中高 | 视部署地而定 | 可用但略重 | 适合 |
| 微信公众号/服务号 | 中高 | 中高 | 很好 | 受限 | 高 | 中 | 可能涉及认证/域名备案 | 个人不省事 | 适合中国市场产品 |
| RSS Feed + RSS 阅读器 | 中 | 低 | 中 | 弱 | 中 | 低 | 高 | 不需要 | 适合作为补充 | 中等 |

---

## 3. 最推荐的个人 MVP 方案

### 3.1 推荐结论

如果目标是“最快上线个人使用”，推荐：

> GitHub Actions 定时任务 + Python 抓取摘要脚本 + 飞书或企业微信机器人推送 + HTML 邮件备份 + Markdown/HTML 静态归档。

如果你主要使用 iPhone，并且愿意安装一个现成推送 App，也可以把推送通道换成：

> GitHub Actions 定时任务 + Python 脚本 + Bark 推送 + 静态 HTML 详情页 + 邮件备份。

### 3.2 为什么这是最省事方案

它避免了：

- 不需要开发 iOS 原生 App。
- 不需要 Xcode。
- 不需要 App Store。
- 不需要 APNs 证书。
- 不需要长期运行 Web 服务器。
- 不需要维护复杂数据库。
- 不需要一开始做账号体系。

它只需要：

- 一个 GitHub 仓库。
- 一个 GitHub Actions 定时任务。
- 一个 LLM API Key。
- 一个推送 Webhook，例如飞书、企业微信、Telegram、Bark、PushPlus、Server 酱。
- 可选一个 SMTP/Resend/SendGrid 邮件发送配置。

### 3.3 手机端体验

手机端可以这样使用：

- 每天早上收到飞书/企业微信/Bark/Telegram 推送。
- 推送中包含今日重点 3 条和每个主题的数量。
- 点击消息中的链接打开当天 HTML 简报。
- 如果不想打开网页，可以在推送消息或邮件正文里直接阅读全文摘要。
- 邮件作为长期归档，方便搜索。
- Markdown 文件作为可迁移数据，未来可导入 Notion、Obsidian 或网站。

---

## 4. 推荐架构

### 4.1 个人 MVP 架构

```text
GitHub Actions Cron
        |
        v
Python daily_digest.py
        |
        +--> Collectors: PubMed / bioRxiv / medRxiv / arXiv / RSS / Web
        |
        +--> Normalize / Deduplicate / Topic Match / Rank
        |
        +--> LLM Chinese Summary
        |
        +--> Render Markdown + HTML + JSON
        |
        +--> Store in repository artifacts or static site folder
        |
        +--> Push: Feishu / WeCom / Bark / Telegram / Email
```

### 4.2 不需要长期运行 FastAPI

个人 MVP 阶段，不建议把 FastAPI 作为必须长期在线服务。

原因：

- 你的需求是每天定时生成简报，不是高频交互 API。
- 定时脚本足够完成抓取、摘要、渲染、推送。
- 少一个在线服务，就少很多部署、监控、故障排查。

FastAPI 可以保留，但作为后续扩展：

- 多人账号。
- 主题管理。
- 在线搜索。
- 收藏和已读。
- PWA 前端 API。

---

## 5. 技术选型建议

### 5.1 抓取与摘要

继续使用 Python。

推荐组件：

- HTTP 请求：httpx。
- RSS 解析：feedparser。
- HTML 抓取：trafilatura 或 BeautifulSoup。
- PDF/全文后续解析：GROBID、PyMuPDF 或 unstructured。
- LLM：OpenAI、Claude、Gemini、DeepSeek、通义千问、智谱等。
- 结构化输出：Pydantic JSON Schema。
- 模板渲染：Jinja2。

当前项目已有可复用模块：

- 主题配置：backend/app/core/topics.py。
- PubMed 采集器：backend/app/services/collectors/pubmed.py。
- bioRxiv 采集器：backend/app/services/collectors/biorxiv.py。
- medRxiv 采集器：backend/app/services/collectors/medrxiv.py。
- arXiv 采集器：backend/app/services/collectors/arxiv.py。
- LLM 摘要骨架：backend/app/services/summarizers/llm.py。
- 每日流水线骨架：backend/app/tasks/daily_pipeline.py。

### 5.2 定时任务

个人 MVP 推荐：GitHub Actions schedule。

优点：

- 免费额度够个人使用。
- 不需要服务器。
- 支持手动运行。
- 支持 Secrets 管理 API Key。
- 日志可查看。

注意：

- GitHub Actions 的定时任务不是精确到秒，可能延迟几分钟到几十分钟。
- Cron 使用 UTC 时间。北京时间早上 8 点，对应 UTC 0 点。
- 公开仓库要避免提交敏感信息。

如果希望更稳定或可视化，可以后续换成：

- Cloudflare Workers Cron。
- Render Cron Job。
- Railway Cron。
- Fly.io Machines + Cron。
- 自己的 VPS + crontab。

### 5.3 内容存储

个人 MVP 推荐三层存储：

1. JSON：机器可读，便于后续搜索、重跑和迁移。
2. Markdown：人类可读，适合 Obsidian、GitHub、Notion 导入。
3. HTML：手机浏览器阅读体验最好。

目录示例：

```text
outputs/
├── 2026-05-19/
│   ├── digest.json
│   ├── digest.md
│   └── index.html
├── 2026-05-20/
│   ├── digest.json
│   ├── digest.md
│   └── index.html
└── latest.html
```

是否需要数据库：

- 个人 MVP：不需要，JSON/SQLite 足够。
- 个人长期使用：SQLite 比较合适。
- 多人产品：PostgreSQL 或 Supabase。

### 5.4 移动端查看

推荐组合：

- 首要入口：飞书/企业微信/Telegram/Bark 推送消息。
- 详细阅读：HTML 邮件或静态 HTML 页面。
- 长期归档：Markdown 文件或 Notion 数据库。

最省事的查看方式：

- 推送正文直接包含摘要。
- 邮件正文包含完整 HTML 简报。
- 不强制打开任何自建网站。

### 5.5 推送通道

按使用环境选择：

#### 国内/中文环境优先

- 飞书机器人：设置简单，移动端体验好，支持富文本卡片。
- 企业微信机器人：设置简单，适合微信群式查看，消息稳定。
- 邮件：最稳定的备份通道。
- Bark：iPhone 推送体验好，适合个人。
- Server 酱/PushPlus：微信生态推送，适合个人但要关注额度和平台规则。

#### 海外或能稳定使用 Telegram

- Telegram Bot：开发最简单，推送很稳定，支持私聊、频道、群组。
- Email：作为备份。

#### 不推荐作为第一选择

- 微信公众号：体验好，但注册、认证、消息规则、模板限制和域名配置都更复杂。
- 原生 iOS App：当前需求下投入不划算。

---

## 6. 几种实现路径详细比较

### 6.1 路径 A：GitHub Actions + 飞书/企业微信机器人 + 邮件

这是最推荐的个人 MVP。

#### 数据流

```text
GitHub Actions 每天定时启动
  -> Python 抓取 PubMed/bioRxiv/medRxiv/arXiv/RSS
  -> 去重和主题匹配
  -> 调用 LLM 生成中文摘要
  -> 生成 digest.md / digest.html / digest.json
  -> 发送飞书/企业微信机器人摘要
  -> 发送 HTML 邮件全文
  -> 可选提交 outputs 到仓库或上传 artifact
```

#### 优点

- 几乎不需要运维。
- 不需要服务器常驻。
- 手机推送及时。
- 邮件可全文阅读和检索。
- 很适合个人每天看简报。
- 成本低，主要是 LLM API 费用。

#### 缺点

- 飞书/企业微信消息长度有限，长内容需要摘要 + 链接或拆分。
- GitHub Actions 定时不是绝对精准。
- 如果用 GitHub Pages 做静态页，国内访问可能不稳定。
- 没有复杂交互，例如收藏、已读、多端同步。

#### 是否需要备案

- 仅机器人推送和邮件：通常不需要。
- 如果静态网页部署在 GitHub Pages、Cloudflare Pages、Vercel、Netlify 等境外服务：通常不需要 ICP 备案，但国内访问稳定性不保证。
- 如果部署在中国大陆服务器并绑定域名：通常需要 ICP 备案。

#### 适合谁

- 最适合个人。
- 也适合 2 到 5 人的小团队内部使用。

---

### 6.2 路径 B：GitHub Actions + Bark + 静态 HTML

如果你只关心 iPhone 推送，这是非常方便的方案。

#### 数据流

```text
GitHub Actions
  -> 生成今日简报 HTML
  -> 部署或保存 HTML
  -> 调用 Bark API 推送标题、摘要和 URL
  -> iPhone 收到系统通知
```

#### 优点

- 不需要开发 iOS App。
- Bark 已经负责 iOS 推送。
- 推送体验接近原生通知。
- 实现极简单，一个 HTTP 请求即可推送。

#### 缺点

- 需要安装 Bark 这个第三方 App。
- 团队协作不如飞书/企业微信自然。
- 长内容还是需要链接到网页或邮件。

#### 是否需要备案

- 只用 Bark 推送：不需要。
- 如果链接到国内自建网页：视服务器所在地而定。

#### 适合谁

- 适合个人 iPhone 用户。
- 不适合直接做多人产品。

---

### 6.3 路径 C：Telegram Bot + 静态页面

如果你能稳定使用 Telegram，这可能是开发体验最好的方案。

#### 优点

- Bot API 简单。
- 支持私聊、群组、频道。
- 支持 Markdown/HTML 消息格式。
- 手机推送稳定。
- 可以做简单交互命令，例如 `/today`、`/topic ai`。

#### 缺点

- 在中国大陆网络环境下通常不方便。
- 面向国内用户产品化不合适。

#### 适合谁

- 海外用户。
- 能稳定使用 Telegram 的个人或小团队。

---

### 6.4 路径 D：纯邮件 Newsletter

这是最稳、最老派、最低维护的方案。

#### 数据流

```text
定时脚本
  -> 生成 HTML 邮件
  -> SMTP/Resend/SendGrid 发送到你的邮箱
  -> 手机邮件 App 推送和阅读
```

#### 优点

- 手机端不需要新 App。
- 长内容排版最好控制。
- 天然可搜索、归档、转发。
- 几乎不需要做前端。
- 稳定性高。

#### 缺点

- 推送体验依赖邮箱 App。
- 即时感不如飞书、企业微信、Bark、Telegram。
- 邮件可能进垃圾箱，需要配置发信域名或白名单。

#### 适合谁

- 非常适合个人长期阅读。
- 适合作为所有方案的备份通道。

---

### 6.5 路径 E：Notion 数据库

#### 数据流

```text
定时脚本
  -> 抓取和摘要
  -> 写入 Notion Database
  -> 手机端 Notion 查看和筛选
  -> 推送用飞书/邮件/Bark 补充
```

#### 优点

- 不用开发前端。
- 适合做知识库。
- 支持标签、筛选、搜索、人工备注。
- 可以长期沉淀文献卡片。

#### 缺点

- Notion API 有速率限制。
- Notion 在国内访问体验可能不稳定。
- Notion 对“自动推送新内容”不是最强，需要其他推送通道配合。

#### 适合谁

- 适合把科研情报沉淀成个人知识库的人。
- 不适合只追求最快推送阅读的人作为唯一方案。

---

### 6.6 路径 F：Obsidian Sync 或 Markdown 仓库

#### 数据流

```text
定时脚本
  -> 生成每日 Markdown
  -> 同步到 Git 仓库、iCloud、Dropbox 或 Obsidian Sync
  -> 手机 Obsidian 查看
```

#### 优点

- 数据完全可控。
- Markdown 可迁移性最好。
- 适合长期知识管理。

#### 缺点

- 推送能力弱。
- 手机端自动同步配置略麻烦。
- 不适合作为唯一“每天提醒我看”的入口。

#### 适合谁

- Obsidian 重度用户。
- 适合作为归档，不适合作为主推送渠道。

---

### 6.7 路径 G：静态网页或 PWA

#### 数据流

```text
定时脚本
  -> 生成静态 JSON/HTML
  -> 部署到 GitHub Pages/Cloudflare Pages/Vercel/Netlify
  -> 手机 Safari 添加到主屏幕
  -> 推送由邮件/飞书/Bark 补充
```

#### 优点

- 手机端接近 App。
- 不需要原生开发。
- 前端可以逐步增强：搜索、主题筛选、收藏、本地缓存。
- 部署便宜。

#### 缺点

- 仍然需要写一点前端。
- iOS PWA 推送虽然支持，但配置 Web Push 比机器人推送复杂。
- 如果数据私密，需要加访问控制。

#### 适合谁

- 适合第二阶段。
- 适合从个人工具慢慢升级为小产品。

---

### 6.8 路径 H：FastAPI 后端 + Web/PWA 前端

#### 数据流

```text
定时任务/队列
  -> FastAPI 抓取和摘要
  -> PostgreSQL/SQLite 存储
  -> Next.js/Vite PWA 查询 API
  -> 手机浏览器查看
  -> 邮件/飞书/企业微信/Web Push 推送
```

#### 优点

- 扩展性最好。
- 可做账号、订阅主题、收藏、已读、搜索。
- 可逐步产品化。
- 可复用当前 FastAPI 项目结构。

#### 缺点

- 比个人 MVP 重。
- 需要部署后端和数据库。
- 需要维护 API、鉴权、前端、监控。

#### 适合谁

- 适合多人产品化。
- 不适合第一天就追求最省事的人。

---

### 6.9 路径 I：微信公众号或微信服务号

#### 优点

- 国内手机端体验很好。
- 用户不用安装新 App。
- 适合产品化和传播。

#### 缺点

- 个人开发不省事。
- 公众号消息能力受平台规则限制。
- 认证、模板消息、菜单、网页授权、服务器配置都有门槛。
- 如果涉及自建网页和国内服务器，可能需要备案。

#### 适合谁

- 不适合最快 MVP。
- 适合后续面向国内用户产品化时考虑。

---

## 7. 推荐的 MVP 数据流

### 7.1 每日任务流程

```text
每天 07:30 或 08:00 北京时间
  1. GitHub Actions 触发 daily_digest.py
  2. 读取主题配置：神经科学、生物材料、AI、骨科
  3. 对每个主题生成查询词
  4. 抓取 PubMed、bioRxiv、medRxiv、arXiv、RSS
  5. 统一成 Article 数据结构
  6. DOI、PMID、标题相似度去重
  7. 主题关键词和语义相似度筛选
  8. 按来源、时间、相关性、质量评分排序
  9. 取每个主题前 N 条
  10. 调用 LLM 生成中文结构化摘要
  11. 生成 JSON、Markdown、HTML
  12. 发送飞书/企业微信/Bark/Telegram 推送
  13. 发送 HTML 邮件全文
  14. 保存输出文件
```

### 7.2 摘要格式

每条内容建议固定输出：

```text
标题：中文标题
来源：PubMed / bioRxiv / medRxiv / arXiv / RSS
主题：神经科学 / 生物材料 / AI / 骨科
一句话结论：...
关键结论：
- ...
- ...
方法亮点：...
价值判断：科研/临床/工程/产品价值
局限性：预印本、样本量、动物实验、回顾性等
原文链接：...
```

每日顶部摘要：

```text
今日重点 3 条
各主题新增数量
最值得读的论文
潜在临床/科研价值最高内容
预印本风险提示
```

---

## 8. 如何复用当前 FastAPI 后端代码

当前项目虽然原本面向 iOS App，但后端模块可以复用。

### 8.1 复用方式一：改成纯定时脚本

保留这些模块：

- `backend/app/core/topics.py`
- `backend/app/services/collectors/*.py`
- `backend/app/services/summarizers/llm.py`
- `backend/app/utils/dedupe.py`

新增：

```text
backend/app/renderers/html_renderer.py
backend/app/renderers/markdown_renderer.py
backend/app/notifiers/feishu.py
backend/app/notifiers/wecom.py
backend/app/notifiers/telegram.py
backend/app/notifiers/email.py
backend/app/notifiers/bark.py
backend/app/tasks/generate_digest.py
.github/workflows/daily-digest.yml
```

这样就不需要长期启动 FastAPI。

### 8.2 复用方式二：保留 FastAPI，增加 Web/PWA

如果你想网页查看，可以保留 FastAPI：

- `GET /api/v1/briefings/today`：今日简报。
- `GET /api/v1/articles`：文章列表和搜索。
- `GET /api/v1/topics`：主题列表。

然后用非常轻的前端：

- Vite + React。
- Next.js。
- Astro。
- 甚至单个 HTML + JavaScript。

手机端直接打开网页，Safari 添加到主屏幕即可。

### 8.3 复用方式三：只用 FastAPI 生成静态页

FastAPI 不对外长期提供服务，只在 GitHub Actions 里运行函数：

```text
run_daily_pipeline()
  -> 返回结构化数据
  -> render HTML
  -> 推送
```

这比长期部署 API 更轻。

---

## 9. 从零到可用的最短实施步骤

下面是个人 MVP 最短路径。

### 第 1 步：砍掉 iOS 原生 App 目标

暂时冻结：

- Xcode 工程。
- SwiftUI 页面。
- APNs。
- 原生收藏、已读、搜索。

保留：

- 后端抓取器。
- 主题配置。
- 摘要服务。
- 每日流水线。

### 第 2 步：创建定时脚本入口

新增一个脚本：

```text
backend/app/tasks/generate_digest.py
```

职责：

- 读取主题。
- 调用采集器。
- 去重。
- 调用 LLM。
- 生成 Markdown/HTML/JSON。
- 调用推送器。

### 第 3 步：实现推送器

优先实现一个即可。

国内推荐二选一：

- 飞书机器人。
- 企业微信机器人。

iPhone 个人推荐：

- Bark。

海外推荐：

- Telegram Bot。

稳定备份：

- Email。

### 第 4 步：生成 HTML 邮件

先不做网页前端，直接用 Jinja2 渲染 HTML 邮件。

优点：

- 手机上阅读很方便。
- 不需要部署网站。
- 邮箱天然归档。

### 第 5 步：配置 GitHub Actions

新增：

```text
.github/workflows/daily-digest.yml
```

配置：

- 每天北京时间早上运行。
- 支持手动运行。
- 从 GitHub Secrets 读取 LLM API Key、Webhook、SMTP 密码。

### 第 6 步：第一次手动运行

在 GitHub Actions 中点 Run workflow。

检查：

- 日志是否抓取成功。
- LLM 是否生成摘要。
- 飞书/企业微信/Bark/Telegram 是否收到推送。
- 邮箱是否收到 HTML 简报。

### 第 7 步：一周内人工校验

每天花 5 分钟检查：

- 主题是否跑偏。
- 摘要是否幻觉。
- 重复内容是否太多。
- 每个主题数量是否合适。
- 推送是否过长。

根据反馈调整：

- 关键词。
- 排除词。
- 每主题条数。
- 摘要 prompt。
- LLM 模型。

---

## 10. MVP 不建议一开始做的事情

不要一开始做：

- 原生 iOS App。
- 复杂 PWA 推送。
- 多用户账号。
- 付费系统。
- 全文 PDF 下载和解析。
- 私有部署向量数据库。
- 复杂文献图谱。
- 微信公众号。
- 微信小程序。

原因：

- 这些都会显著增加开发和维护成本。
- 你的核心价值是“每日内容质量”，不是 App 外壳。
- 先用推送和邮件验证内容质量最划算。

---

## 11. 费用估算

个人 MVP：

| 项目 | 费用 |
|---|---:|
| GitHub Actions | 通常免费额度够用 |
| 飞书/企业微信机器人 | 通常免费 |
| Bark | App 或服务可能有少量成本，视使用方式而定 |
| Telegram Bot | 免费 |
| 邮件 SMTP | 个人邮箱免费，Resend/SendGrid 有免费额度 |
| LLM API | 主要成本，取决于每天文章数量和模型 |
| 静态托管 | GitHub Pages/Cloudflare Pages 通常免费 |
| 域名 | 可选，几十元到百元级每年 |
| 数据库 | MVP 不需要 |

控制 LLM 成本的方法：

- 先规则筛选，再摘要，不要对所有抓取结果摘要。
- 每个主题每天只摘要前 5 到 10 条。
- 先用便宜模型生成初稿。
- 只对重点内容调用更强模型。
- 缓存 DOI/PMID，避免重复摘要。

---

## 12. 稳定性建议

### 12.1 多通道推送

建议至少两个通道：

- 主通道：飞书/企业微信/Bark/Telegram。
- 备份通道：Email。

这样即使一个通道失败，也能看到简报。

### 12.2 错误处理

定时脚本要支持：

- 单个数据源失败不影响整体。
- LLM 失败时保留原摘要。
- 推送失败时发邮件告警。
- 每次运行生成日志。

### 12.3 数据源限速

需要注意：

- PubMed/NCBI 建议配置 email 和 API key。
- arXiv API 不要高频请求。
- bioRxiv/medRxiv API 控制请求频率。
- RSS 和网页抓取要遵守 robots 和使用条款。

---

## 13. 备案和合规建议

### 13.1 个人私用

以下通常不需要备案：

- GitHub Actions 定时运行。
- 机器人推送到你自己的飞书/企业微信/Telegram。
- 邮件发送给自己。
- Notion 私人数据库。
- Obsidian 私人笔记。
- GitHub Pages/Cloudflare Pages 等境外托管静态页。

注意：境外静态页通常不需要 ICP 备案，但国内访问速度和稳定性不一定。

### 13.2 使用中国大陆服务器或域名

如果你用中国大陆服务器提供网页服务并绑定域名，通常需要 ICP 备案。

如果后续做多人产品，还要考虑：

- 用户隐私政策。
- 数据处理说明。
- 版权和原文链接规范。
- 论文摘要和新闻内容的合理使用边界。
- 预印本未同行评议提示。

### 13.3 微信公众号/小程序

微信公众号和小程序会涉及更多平台规则：

- 主体认证。
- 域名配置。
- 服务器校验。
- 消息模板限制。
- 网页授权。
- 可能涉及备案。

所以不建议作为第一版 MVP。

---

## 14. 如果后续要做成多人可用产品

如果个人 MVP 验证成功，再升级成产品化方案。

### 14.1 推荐产品化架构

```text
Collectors / Workers
        |
        v
FastAPI Backend  ---- PostgreSQL / pgvector
        |
        +---- Redis Queue
        |
        +---- LLM Summary Service
        |
        +---- Notification Service: Email / Feishu / WeCom / Telegram / Web Push
        |
        v
Web / PWA Frontend
        |
        v
Mobile Safari / Chrome / Add to Home Screen
```

### 14.2 技术选型

后端：

- FastAPI。
- PostgreSQL。
- Redis。
- Celery/RQ/Arq。
- pgvector 可选。

前端：

- Next.js 或 Vite + React。
- PWA 支持。
- 移动端响应式 UI。

部署：

- 小规模海外：Render、Railway、Fly.io、Vercel、Supabase、Neon。
- Cloudflare：Pages、Workers、R2、D1，适合轻量全球部署。
- 国内用户：阿里云/腾讯云/华为云 + 备案。

通知：

- Email 必备。
- 飞书/企业微信适合团队。
- Telegram 适合海外。
- PWA Web Push 可作为后续增强。

账号：

- Supabase Auth。
- Clerk。
- Auth.js。
- 自建 JWT 登录。

### 14.3 产品化功能顺序

1. Web/PWA 今日简报。
2. 用户主题订阅。
3. 收藏和已读。
4. 搜索和标签。
5. 推送偏好。
6. 个性化排序。
7. 团队共享。
8. 支付和权限。

---

## 15. 最终建议

### 15.1 只想最快上线个人使用

选择：

> GitHub Actions 定时脚本 + 飞书/企业微信机器人或 Bark 推送 + HTML 邮件备份 + Markdown/HTML 归档。

建议默认组合：

- 国内和团队沟通习惯：飞书机器人 + 邮件。
- 纯 iPhone 个人推送：Bark + 邮件。
- 海外或 Telegram 用户：Telegram Bot + 邮件。

这是最省事、最快可用、维护成本最低的方案。

### 15.2 想保留未来扩展空间

选择：

> 先把当前 FastAPI 后端里的抓取、主题、摘要逻辑改造成可被定时任务调用的模块，同时输出静态 HTML/Markdown；后续再加 Web/PWA 前端。

这样不会浪费当前项目结构，也不会被 iOS 原生开发拖慢。

### 15.3 以后想做成多人可用产品

选择：

> FastAPI + PostgreSQL + Redis Worker + Web/PWA + 邮件/飞书/企业微信/Telegram 多通道推送。

不要优先回到 iOS 原生 App。除非后续已经验证有大量稳定用户，并且明确需要原生能力，否则 Web/PWA 足够覆盖绝大多数科研情报阅读场景。
