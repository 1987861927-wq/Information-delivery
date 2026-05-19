# 架构说明

```text
iOS SwiftUI App
      |
      v
FastAPI REST API ---- PostgreSQL/pgvector
      |
      +---- Redis Queue / Scheduler
      |
      +---- Collectors: PubMed, bioRxiv, medRxiv, arXiv, RSS
      |
      +---- LLM Summarizer
      |
      +---- APNs Push Service
```

## 模块职责

- `api`：对 iOS 提供主题、文章、简报、收藏、推送设置接口。
- `models`：数据库领域模型。
- `schemas`：API 请求与响应模型。
- `services.collectors`：外部数据源采集器。
- `services.summarizers`：中文结构化摘要生成。
- `tasks`：每日采集、摘要和推送任务。
- `core`：配置、日志、常量。

## 第一阶段落地策略

先用内存样例和轻量采集器跑通端到端流程，再切换到 PostgreSQL 与队列任务。
