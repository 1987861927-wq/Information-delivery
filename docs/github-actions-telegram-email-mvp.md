# GitHub Actions + Telegram Bot + 邮件推送科研情报 MVP

本指南说明如何使用当前仓库中的自动化流水线，实现无需长期服务器、每天自动运行、通过 Telegram 和邮箱在手机端阅读的科研情报日报。

## 1. 这个方案做什么

每天定时完成：

1. 抓取 PubMed、arXiv、RSS、bioRxiv、medRxiv、GitHub、NIH RePORTER。
2. 按神经科学、生物材料、人工智能、骨科四个主题筛选。
3. 去重、排序，并按主题选出高相关内容。
4. 生成中文摘要、关键结论、方法或技术亮点、科研或临床价值判断。
5. 保存 Markdown、HTML、JSON 日报。
6. 发送 Telegram 推送。
7. 发送 HTML/Markdown 邮件。
8. 在 GitHub Actions 中上传日报 artifact，方便追溯。

当前不需要：

- iOS 原生 App。
- App Store。
- APNs。
- 长期运行服务器。
- 数据库。

## 2. 目录结构

```text
research-intelligence-ios/
├── automation/                         # 自动化流水线核心模块
│   ├── collectors/                      # PubMed、arXiv、RSS、bioRxiv、medRxiv、GitHub、NIH RePORTER 抓取器
│   ├── notifiers/                       # Telegram 和邮件发送
│   ├── renderers/                       # Markdown/HTML/Telegram 预览渲染
│   ├── config_loader.py                 # YAML 和 .env 配置读取
│   ├── models.py                        # Article、Digest 等数据模型
│   ├── processing.py                    # 主题匹配、去重、排序
│   ├── summarizer.py                    # 规则摘要和 OpenAI 兼容 LLM 摘要
│   └── utils.py                         # 日志、日期、文本工具
├── config/
│   ├── topics.yml                       # 主题、关键词、推送时间等配置
│   ├── sources.yml                      # 数据源、RSS Feed 和 top 期刊筛选策略
│   └── journals.yml                     # 本地维护的 top 期刊 IF/白名单目录
├── scripts/
│   ├── daily_digest.py                  # 本地和 Actions 主入口
│   └── self_check.py                    # 最小自检脚本
├── data/digests/YYYY-MM-DD/             # 每天生成的 digest.md/html/json
├── .github/workflows/daily-digest.yml   # GitHub Actions 定时任务
├── requirements-automation.txt          # 自动化流水线依赖
└── .env.example                         # 本地环境变量示例
```

## 3. 配置主题和数据源

主题配置在：

```text
config/topics.yml
```

默认包含：

- `neuroscience`：神经科学。
- `biomaterials`：生物材料。
- `ai`：人工智能。
- `orthopedics`：骨科。

你可以修改：

- `keywords`：通用关键词，用于 RSS、预印本和统一主题匹配。
- `exclude_keywords`：排除词。
- `pubmed_query`：PubMed 专用检索式。
- `arxiv_query`：arXiv 专用检索式。
- `max_items`：每个主题每天最多保留几条。

数据源配置在：

```text
config/sources.yml
```

默认启用：

- PubMed：使用 NCBI E-utilities。
- arXiv：使用官方 API。
- RSS：使用 feedparser 解析多个 RSS Feed。
- bioRxiv：使用 bioRxiv API。
- medRxiv：使用 medRxiv API。
- GitHub：使用 GitHub REST API 搜索相关 repositories，并可读取 latest release。
- NIH RePORTER：使用 NIH RePORTER API 搜索资助项目和 grant。

说明：

- PubMed 建议配置 `NCBI_EMAIL`，如果频繁请求建议配置 `NCBI_API_KEY`。
- arXiv 官方 API 对请求频率敏感，配置中保留了请求延迟。
- bioRxiv/medRxiv API 偶尔可能超时或返回不稳定，单源失败不会导致整个日报失败，会在日报中写入异常提示。
- RSS 源可以自由增加，只需要填写 `name`、`url`、`topics`。
- GitHub 可选配置 `GITHUB_TOKEN` 提高 REST API 限额；未配置时仍可低限额访问公开仓库搜索。
- NIH RePORTER 当前不需要 token；可在 `config/sources.yml` 中按财政年度、机构、PI、关键词缩小范围。

### 3.1 top 期刊和 IF 筛选

当前支持基于本地期刊目录进行 top 期刊优先排序或硬过滤：

- `config/sources.yml` 中的 `top_journal_filter` 控制策略。
- `config/journals.yml` 维护期刊名称、别名、近似 IF、分层标签和白名单。
- 默认 `mode=rank`：不硬过滤，只给 IF 较高或白名单期刊更高排序权重，并在日报中展示 `IF≈xx`。
- `mode=push`：抓取后只保留 `impact_factor >= min_impact_factor` 的期刊内容；未知 IF 内容默认排除。
- `mode=fetch-and-push`：PubMed 抓取阶段追加 top 期刊 Journal 检索式，然后再执行 `push` 过滤。
- `mode=off`：关闭 top 期刊逻辑。

建议先使用默认 `rank` 观察真实日报质量；确认期刊目录覆盖足够后，再手动运行 `push` 或 `fetch-and-push`。

注意：期刊 IF 每年变化，精确官方 IF 可能需要授权数据；当前 `config/journals.yml` 是可审计、可维护的近似过滤表，适合 MVP 筛选边界，不应视为官方 JCR 数据源。

## 4. 本地运行

### 4.1 安装依赖

```bash
cd /mnt/f/AI2/research-intelligence-ios
python3 -m venv .venv-automation
source .venv-automation/bin/activate
pip install -r requirements-automation.txt
cp .env.example .env
```

### 4.2 先跑自检，不访问外部数据源

```bash
python scripts/self_check.py
```

该命令会使用样例数据生成：

```text
data/digests/2026-01-01/digest.md
```

### 4.3 生成预览，不发送 Telegram 和邮件

```bash
python scripts/daily_digest.py --no-fetch --preview --skip-telegram --skip-email
```

### 4.4 抓取真实数据但不推送

```bash
python scripts/daily_digest.py --preview --skip-telegram --skip-email
```

### 4.5 只运行指定主题

```bash
python scripts/daily_digest.py --topics ai neuroscience --max-items 3 --preview
```

### 4.6 指定日报日期和抓取天数

```bash
python scripts/daily_digest.py --date 2026-05-19 --days-back 2 --preview
```

### 4.7 本地验证 top 期刊筛选

仅本地样例数据，不访问外部数据源：

```bash
python scripts/daily_digest.py --no-fetch --preview --skip-telegram --skip-email --top-journal-mode push --min-impact-factor 10
```

真实抓取但不推送，观察 IF 标记和筛选结果：

```bash
python scripts/daily_digest.py --preview --skip-telegram --skip-email --top-journal-mode rank --min-impact-factor 10
```

只推送 IF 大于等于 10 的内容，可使用：

```bash
python scripts/daily_digest.py --top-journal-mode push --min-impact-factor 10 --skip-email
```

如果希望 PubMed 抓取阶段就限制 top 期刊，可使用：

```bash
python scripts/daily_digest.py --top-journal-mode fetch-and-push --min-impact-factor 10 --skip-email
```

## 5. 摘要模式

### 5.1 无大模型 API Key

如果没有配置 `OPENAI_API_KEY`，脚本会使用规则模板摘要：

- 基于标题和 abstract 生成基础中文概述。
- 抽取前几句作为关键结论。
- 根据关键词猜测方法亮点和应用价值。
- 明确提示这是规则摘要，未做全文事实校验。

优点：免费、稳定。

缺点：中文质量和分析深度有限。

### 5.2 配置 OpenAI 或兼容接口

`scripts/daily_digest.py` 会在生成每条内容摘要时调用 `automation/summarizer.py`：

- 未配置 `OPENAI_API_KEY`：使用规则中文摘要，并在日志中输出“未配置 OPENAI_API_KEY，使用规则中文摘要兜底”。
- 已配置 `OPENAI_API_KEY`：调用 OpenAI 兼容 Chat Completions 接口。
- LLM 请求失败、超时、接口返回非 JSON 或模型输出字段不完整：自动回退规则摘要，并把失败原因写入局限性提示。

设置环境变量：

```text
OPENAI_API_KEY
OPENAI_BASE_URL
OPENAI_MODEL
OPENAI_TIMEOUT_SECONDS
```

默认：

```text
OPENAI_BASE_URL=https://api.openai.com/v1
OPENAI_MODEL=gpt-4o-mini
```

如果使用兼容 OpenAI Chat Completions 的服务，可以修改 `OPENAI_BASE_URL` 和 `OPENAI_MODEL`。兼容服务必须支持：

```text
POST {OPENAI_BASE_URL}/chat/completions
```

并且模型需要能够稳定输出 JSON object。

脚本要求模型输出严格 JSON，并包含：

- `brief`
- `key_conclusions`
- `method_highlights`
- `value_judgement`
- `limitations`

如果 LLM 失败，会自动回退到规则摘要，并在日志中提示。

本地运行时可写入 `.env`；GitHub Actions 运行时配置为 repository secrets。不要把真实 API Key 写入仓库或 artifact。

## 6. 创建 Telegram Bot

1. 打开 Telegram。
2. 搜索 `@BotFather`。
3. 发送：

```text
/newbot
```

4. 按提示输入 bot 名称和用户名。
5. BotFather 会返回 Bot Token，形如：

```text
123456789:ABCDEFxxxxxxxxxxxxxxxxxxxx
```

这个值配置为 GitHub Secret：

```text
TELEGRAM_BOT_TOKEN
```

## 7. 获取 Telegram Chat ID

### 7.1 私聊推送

1. 打开你刚创建的 Bot。
2. 点击 Start 或发送任意消息，例如 `hello`。
3. 在浏览器打开：

```text
https://api.telegram.org/bot你的BotToken/getUpdates
```

4. 返回 JSON 中找到：

```json
"chat":{"id":123456789}
```

这个数字就是：

```text
TELEGRAM_CHAT_ID
```

### 7.2 群组推送

1. 把 Bot 加入群组。
2. 在群里发一条消息并 @bot。
3. 打开 `getUpdates`。
4. 群组 chat id 通常是负数，例如：

```text
-1001234567890
```

把它配置为 `TELEGRAM_CHAT_ID`。

## 8. 配置邮箱 SMTP

需要准备：

```text
SMTP_HOST
SMTP_PORT
SMTP_USERNAME
SMTP_PASSWORD
SMTP_FROM
SMTP_TO
SMTP_USE_TLS
SMTP_USE_SSL
```

常见示例：

### 8.1 Gmail

Gmail 通常需要开启两步验证，并使用 App Password。

```text
SMTP_HOST=smtp.gmail.com
SMTP_PORT=587
SMTP_USE_TLS=true
SMTP_USE_SSL=false
SMTP_USERNAME=your@gmail.com
SMTP_PASSWORD=你的AppPassword
SMTP_FROM=your@gmail.com
SMTP_TO=your@gmail.com
```

### 8.2 QQ 邮箱

QQ 邮箱通常使用授权码，不是登录密码。

```text
SMTP_HOST=smtp.qq.com
SMTP_PORT=465
SMTP_USE_TLS=false
SMTP_USE_SSL=true
SMTP_USERNAME=你的QQ邮箱@qq.com
SMTP_PASSWORD=授权码
SMTP_FROM=你的QQ邮箱@qq.com
SMTP_TO=接收邮箱@example.com
```

### 8.3 163 邮箱

同样通常需要授权码。

```text
SMTP_HOST=smtp.163.com
SMTP_PORT=465
SMTP_USE_TLS=false
SMTP_USE_SSL=true
SMTP_USERNAME=你的邮箱@163.com
SMTP_PASSWORD=授权码
SMTP_FROM=你的邮箱@163.com
SMTP_TO=接收邮箱@example.com
```

## 9. GitHub Secrets 命名清单

在 GitHub 仓库中打开：

```text
Settings → Secrets and variables → Actions → New repository secret
```

建议配置：

### 必填推送配置

```text
TELEGRAM_BOT_TOKEN
TELEGRAM_CHAT_ID
SMTP_HOST
SMTP_PORT
SMTP_USERNAME
SMTP_PASSWORD
SMTP_FROM
SMTP_TO
SMTP_USE_TLS
SMTP_USE_SSL
```

### 可选 LLM 配置

```text
OPENAI_API_KEY
OPENAI_BASE_URL
OPENAI_MODEL
OPENAI_TIMEOUT_SECONDS
```

### 可选 PubMed 配置

```text
NCBI_EMAIL
NCBI_API_KEY
```

### 可选 GitHub 配置

```text
GITHUB_TOKEN
```

`GITHUB_TOKEN` 用于提高 GitHub REST API rate limit；不配置时 GitHub connector 仍会用未认证低限额请求公开仓库。

如果暂时没有 LLM Key，可以不配置 `OPENAI_API_KEY`，系统会自动使用规则摘要。

如果暂时只想用 Telegram，可以不配置 SMTP；如果只想用邮件，可以在手动触发时勾选跳过 Telegram。

### top 期刊筛选无需 Secrets

`top_journal_filter` 使用仓库中的 `config/sources.yml` 和 `config/journals.yml`，不需要配置 GitHub Secrets。手动触发 Actions 时可以填写：

```text
top_journal_mode=rank
top_journal_mode=push
top_journal_mode=fetch-and-push
min_impact_factor=10
keep_unknown_if=false
```

## 10. GitHub Actions 自动运行

Workflow 文件：

```text
.github/workflows/daily-digest.yml
```

默认计划：

```text
0 0 * * *
```

GitHub Actions 使用 UTC，`00:00 UTC` 约等于北京时间 `08:00`。

定时任务的默认策略：

- 自动抓取真实数据。
- 自动推送 Telegram。
- 自动追加 `--skip-email`，避免 SMTP 未配置时影响 Telegram-only MVP。
- 使用 `config/sources.yml` 中的 top 期刊策略，默认 `rank`。
- 如果 workflow 失败，并且 Telegram secrets 已配置，会额外发送一条失败告警消息，包含 Actions run 链接。

Workflow 支持手动触发：

1. 打开 GitHub 仓库。
2. 进入 Actions。
3. 选择 `Daily Research Digest`。
4. 点击 `Run workflow`。
5. 可选填写日期、主题、最大条目数、top 期刊模式和 IF 阈值。
6. 点击运行。

运行完成后，在 workflow 的 artifact 中可以下载：

- `digest.md`
- `digest.html`
- `digest.json`

### 10.1 推荐 Actions 验证参数

Telegram-only 定时等价验证：

```text
preview=false
skip_telegram=false
skip_email=true
top_journal_mode=rank
min_impact_factor=10
```

只验证 top 期刊硬过滤，不发推送：

```text
preview=true
skip_telegram=true
skip_email=true
top_journal_mode=push
min_impact_factor=10
```

邮件验证：

```text
preview=false
skip_telegram=true
skip_email=false
```

完整推送：

```text
preview=false
skip_telegram=false
skip_email=false
```

## 11. 常见错误排查

### 11.1 Telegram 没收到

检查：

- `TELEGRAM_BOT_TOKEN` 是否正确。
- `TELEGRAM_CHAT_ID` 是否正确。
- 你是否先给 Bot 发过 `/start`。
- 如果是群组，Bot 是否在群里。
- Actions 日志中是否有 Telegram API 报错。

### 11.2 邮件没收到

检查：

- SMTP 密码是否是授权码，不是网页登录密码。
- `SMTP_USE_TLS` 和 `SMTP_USE_SSL` 是否与端口匹配。
- `SMTP_FROM` 是否与账号一致。
- 垃圾箱中是否有邮件。
- 邮箱服务是否禁止第三方 SMTP。

### 11.3 PubMed 抓取失败

建议：

- 配置 `NCBI_EMAIL`。
- 降低 retmax 或增加请求间隔。
- 查看 Actions 日志中具体 HTTP 错误。

### 11.4 arXiv 抓取失败

建议：

- arXiv API 不要高频请求。
- 保留 `request_delay_seconds`。
- 简化过长或过复杂的 `arxiv_query`。

### 11.5 LLM 摘要失败

脚本会自动回退规则摘要。

检查：

- `OPENAI_API_KEY` 是否有效。
- `OPENAI_BASE_URL` 是否兼容 `/chat/completions`。
- `OPENAI_MODEL` 是否存在。
- 账号是否有余额或访问权限。

### 11.6 GitHub 或 NIH RePORTER 内容太少

检查：

- `config/sources.yml` 中 `github.enabled` 和 `nih_reporter.enabled` 是否为 `true`。
- GitHub 是否触发未认证 API 限流；需要时配置 `GITHUB_TOKEN`。
- `github.min_score`、`github.min_stars`、`github.stale_days` 是否过严。
- `nih_reporter.min_score`、`nih_reporter.fiscal_years`、`nih_reporter.agencies`、`nih_reporter.organizations`、`nih_reporter.pis` 是否限制过窄。
- 新来源结果会先进入统一 `Article` schema，再经过主题匹配、去重、排序和 Telegram 预览截断。

### 11.7 top 期刊过滤后内容太少

检查：

- `config/journals.yml` 是否包含目标期刊的全称和 PubMed 缩写别名。
- `min_impact_factor` 是否过高。
- `top_journal_mode=push` 是否把 arXiv、bioRxiv、medRxiv 等未知 IF 来源排除了。
- 是否需要在 `keep_unknown_if_sources` 中临时保留预印本来源。
- 是否应先使用 `rank` 模式观察一段时间，再切换到 `push`。

### 11.8 单个数据源失败

单个数据源失败不会让整条流水线失败。日报中会出现“数据源异常提示”。

但如果配置文件错误、依赖安装失败、渲染失败或推送接口抛出未处理错误，GitHub Actions 会失败，以便你及时发现问题。

## 12. 后续扩展方向

可以逐步增加：

- 静态网页发布。
- RSS 输出。
- Notion 数据库写入。
- 飞书或企业微信机器人。
- SQLite 缓存，避免重复摘要。
- 基于 DOI/PMID 的长期去重。
- Web/PWA 前端。
