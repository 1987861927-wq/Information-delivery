# Research Intelligence iOS

面向神经科学、生物材料、AI、骨科等方向的 iOS 科研情报 App 骨架。

## MVP 能力

- 每日抓取 PubMed、bioRxiv、medRxiv、arXiv 等来源的新论文与前沿资讯。
- 按主题规则进行归类、去重、质量评分。
- 调用 LLM 生成中文结构化摘要。
- iOS App 展示今日简报、主题、详情、收藏和搜索。
- 后续接入 APNs 推送每日简报。


## 当前推荐 MVP：GitHub Actions + Telegram + 邮件

项目已新增无需 iOS 原生 App、无需长期服务器的科研情报自动化方案：

- 主入口脚本：`scripts/daily_digest.py`
- 自动化模块：`automation/`
- 主题配置：`config/topics.yml`
- 数据源配置：`config/sources.yml`
- GitHub Actions：`.github/workflows/daily-digest.yml`
- 使用指南：`docs/github-actions-telegram-email-mvp.md`

本方案每天自动抓取 PubMed、arXiv、RSS、bioRxiv、medRxiv，生成中文 Markdown/HTML 日报，并通过 Telegram Bot 与邮件推送到手机端。原 iOS SwiftUI 代码保留为后续可选扩展，不再作为第一优先级。

## 目录

- `backend/`：FastAPI 后端、采集器、摘要服务、任务调度。
- `ios/ResearchIntelApp/`：SwiftUI iOS App 代码骨架。
- `docs/`：产品计划、架构说明和后续任务。

## 快速启动后端

```bash
cd backend
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
cp .env.example .env
uvicorn app.main:app --reload
```

访问：

- 健康检查：`http://127.0.0.1:8000/health`
- 主题列表：`http://127.0.0.1:8000/api/v1/topics`
- 今日简报：`http://127.0.0.1:8000/api/v1/briefings/today`

## 注意

当前是可迭代开发骨架，采集器优先实现公开 API 与 RSS 方式；正式部署前需要补充数据库迁移、鉴权、APNs 证书、LLM API Key、监控告警和数据源使用条款审查。
