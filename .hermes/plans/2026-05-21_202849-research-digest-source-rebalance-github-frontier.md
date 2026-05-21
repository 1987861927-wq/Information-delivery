# 科研日报来源排序与 GitHub 前沿模式实施计划

## Goal

解决 `research-intelligence-ios` 每日自动日报中两个体验问题：

1. NIH RePORTER 项目因评分尺度过高，容易在“今日重点”和主题条目中压过论文/预印本/资讯。
2. GitHub 来源当前按科研主题关键词检索，而用户希望它独立关注“前沿开源项目/工具”，不必强相关 neuroscience、biomaterials、orthopedics 等主题词。

本计划只规划，不执行代码修改。

## Current context / assumptions

项目路径：

```text
/mnt/f/ai2/research-intelligence-ios
```

当前推荐 MVP 是：

```text
GitHub Actions → scripts/daily_digest.py → automation/ → Markdown/HTML/JSON → Telegram/Email
```

已审查的关键文件：

```text
scripts/daily_digest.py
automation/processing.py
automation/collectors/github.py
automation/collectors/nih_reporter.py
automation/renderers/markdown.py
automation/renderers/html.py
config/topics.yml
config/sources.yml
scripts/self_check.py
```

当前 Git 状态中已有未提交修改：

```text
automation/processing.py
scripts/self_check.py
```

注意：这些修改不是本计划执行产生的。正式修改前必须先查看 diff，避免覆盖或误改用户已有变更。

## Problem diagnosis

### Problem 1: NIH RePORTER 容易显得过度优先

观察到 2026-05-19 的 digest 中，主题内 NIH 并非全部占满，但“今日重点”前两条是 NIH，造成用户感知为 NIH 主导。

根因：

1. NIH `importance_score` 由关键词、fiscal year、award amount、agency、terms 加权，常达到 7-9。
2. PubMed/arXiv/bioRxiv/RSS 多数 relevance_score 约 1-3。
3. `renderers/markdown.py::_pick_highlights()` 直接按：

```python
(relevance_score, quality_score, journal_impact_factor)
```

排序，没有来源上限或来源优先级。

4. `automation/processing.py::_select_diverse_articles()` 会先按来源多样性选择，每个 source 给一个机会，NIH 因分数高通常排在主题内第一。
5. NIH 是资助项目信息，不等同于每日论文/预印本/科研资讯，应更适合作为补充信号或趋势观察。

### Problem 2: GitHub 当前是 topic-based，而不是 frontier-based

当前 `automation/collectors/github.py`：

1. 对每个 topic 循环。
2. 默认 query 来自 `topic.keywords[:8]`。
3. `_hotness_score()` 把 topic keywords 命中作为基础分。
4. `_repo_to_article()` 返回 `topics=[topic.slug]`。

这会导致 GitHub 变成“每个科研主题下的相关仓库”，不是用户想要的“独立关注前沿开源项目”。

## Proposed architecture

采用保守、可回退方案：

1. 不删除 NIH，不关闭 NIH。
2. NIH 继续采集，但默认作为 supplemental source。
3. 今日重点限制 NIH 数量，避免首页被 NIH 占据。
4. 主题内选择增加来源策略：优先论文/预印本/RSS/GitHub，NIH 作为补充。
5. GitHub 增加 `frontier` 模式：不按 topic keywords，而按独立配置的 frontier queries 抓取。
6. GitHub 前沿内容放入单独虚拟主题 `github_frontier`，不抢占 neuroscience/AI/biomaterials/orthopedics 的主题名额。
7. 保留原 topic 模式作为可回退配置。

## Files likely to change

### Core code

```text
automation/processing.py
```

可能修改：

- `_article_sort_key()` 增加 source priority/display score 支持。
- `_select_diverse_articles()` 增加 supplemental source 处理。
- `select_items_by_topic()` 支持配置或默认来源策略。

```text
automation/renderers/markdown.py
```

可能修改：

- `_pick_highlights()` 增加来源上限、NIH 降权或 exclude_from_highlights 逻辑。
- `render_telegram_preview()` 如需确保 GitHub 前沿在 Telegram 中合理展示，也可能小改。

```text
automation/renderers/html.py
```

可能修改：

- 如果 GitHub 前沿主题需要特殊样式，才修改；否则不动。

```text
automation/collectors/github.py
```

可能修改：

- 增加 `mode`：`topic` / `frontier`。
- 增加 `_collect_github_topic_mode()` 与 `_collect_github_frontier_mode()`。
- 增加 `_build_frontier_queries()`。
- 改造 `_hotness_score()`，让 frontier 模式不依赖 topic keywords。
- 让 frontier 结果进入 `topics=[github_frontier]`。

```text
scripts/daily_digest.py
```

可能修改：

- 如果 `select_items_by_topic()` 需要 sources_config 传入，需要调整调用。
- 若 topics.yml 不含 github_frontier，可在运行时动态追加 topic；但更推荐显式写入 topics.yml。

### Config

```text
config/topics.yml
```

可能新增：

```yaml
- slug: github_frontier
  name: GitHub 前沿
  description: 前沿开源项目、AI 工具、科研基础设施和开发者生态趋势。
  max_items: 5
  keywords: []
  exclude_keywords: []
```

```text
config/sources.yml
```

可能调整：

```yaml
nih_reporter:
  enabled: true
  max_results_per_topic: 6
  display_role: supplemental
  max_items_per_topic: 1
  exclude_from_highlights: true
  score_multiplier: 0.4
```

可能新增 GitHub frontier 配置：

```yaml
github:
  enabled: true
  mode: frontier
  frontier_topic_slug: github_frontier
  max_frontier_items: 5
  frontier_queries:
    - 'topic:llm stars:>100 pushed:>2026-01-01 archived:false'
    - 'topic:agents stars:>50 pushed:>2026-01-01 archived:false'
    - 'topic:rag stars:>50 pushed:>2026-01-01 archived:false'
    - 'topic:machine-learning stars:>200 pushed:>2026-01-01 archived:false'
    - 'topic:scientific-computing stars:>50 pushed:>2026-01-01 archived:false'
```

注意：`pushed:>YYYY-MM-DD` 不宜写死在长期配置中。更好的实现是在代码中支持相对日期，例如 `frontier_days_back: 30`，运行时动态拼接 pushed 限制。

### Tests / self-check

```text
scripts/self_check.py
```

可能新增：

- NIH 不应连续占据今日重点。
- NIH 作为 supplemental source，主题内最多 1 条。
- GitHub frontier repo 即使不命中科研 topic keywords，也可入选 `github_frontier`。

可能新增测试文件，若项目当前没有正式 pytest for automation：

```text
tests/test_processing.py
```

但当前 automation 侧主要靠 `scripts/self_check.py`，可优先扩展 self_check，避免引入新的测试结构。

## Step-by-step implementation plan

### Task 0: Preflight inspection

Objective: 正式修改前确认当前未提交变更内容，避免覆盖用户已有修改。

Read-only commands:

```bash
git status --short
git diff -- automation/processing.py scripts/self_check.py
```

Expected:

- 明确当前已有改动是什么。
- 若 diff 很大或与本任务冲突，先暂停并询问用户。

### Task 1: Add source policy helpers

Objective: 在 `automation/processing.py` 中增加来源策略辅助函数，但先不改变主流程太多。

Likely additions:

```python
DEFAULT_SUPPLEMENTAL_SOURCES = {"NIH RePORTER"}
DEFAULT_SOURCE_PRIORITY = {
    "PubMed": 100,
    "bioRxiv": 90,
    "medRxiv": 88,
    "arXiv": 86,
    "RSS": 75,
    "GitHub": 70,
    "NIH RePORTER": 45,
}
```

Add helper:

```python
def source_priority(source: str) -> int:
    return DEFAULT_SOURCE_PRIORITY.get(source, 50)
```

Add helper:

```python
def display_score(article: Article) -> float:
    if article.source == "NIH RePORTER":
        return min(article.relevance_score, 3.0)
    return article.relevance_score
```

Tradeoff:

- 用 `display_score` 不破坏 metadata 原始分。
- NIH 原始 importance_score 仍保留在 metadata。

### Task 2: Limit NIH in highlights

Objective: 避免“今日重点”被 NIH 主导。

Modify:

```text
automation/renderers/markdown.py::_pick_highlights
```

Proposed behavior:

- 默认 top 3 highlights。
- NIH 最多 1 条，或配置为 exclude 时 0 条。
- 优先展示非 NIH 的高分论文/预印本/RSS/GitHub。

Possible implementation:

```python
def _pick_highlights(digest: Digest) -> list[DigestItem]:
    all_items = [item for items in digest.items_by_topic.values() for item in items]
    all_items.sort(key=_highlight_sort_key, reverse=True)
    selected = []
    source_counts = {}
    for item in all_items:
        source = item.article.source
        if source == "NIH RePORTER" and source_counts.get(source, 0) >= 1:
            continue
        selected.append(item)
        source_counts[source] = source_counts.get(source, 0) + 1
        if len(selected) >= 3:
            break
    return selected
```

Better key:

```python
(source_priority, display_score, quality_score, journal_if)
```

Need to avoid circular import if helpers are in processing.py. Options:

1. Put simple local helper in markdown.py.
2. Move scoring helpers to `automation/source_policy.py`.

Recommended minimal approach:

- Add local `_highlight_sort_key()` and `_source_priority()` in markdown.py first.
- Avoid broader refactor.

### Task 3: Adjust topic selection to treat NIH as supplemental

Objective: 主题正文中 NIH 不再因高分稳定排第一或占据过多名额。

Modify:

```text
automation/processing.py::_select_diverse_articles
```

Behavior:

- Split sorted_articles into primary and supplemental.
- First select primary sources with diversity.
- Then fill remaining slots with supplemental sources.
- Cap NIH per topic to 1 by default.

Pseudo:

```python
primary = [a for a in sorted_articles if a.source not in supplemental_sources]
supplemental = [a for a in sorted_articles if a.source in supplemental_sources]
selected = diverse_select(primary, limit)
if len(selected) < limit:
    selected.extend(supplemental[: limit - len(selected)])
```

Need cap:

```python
max_supplemental_per_source = {"NIH RePORTER": 1}
```

Keep YAGNI:

- Start with defaults in code.
- Only add full config wiring if needed after first tests.

### Task 4: Add GitHub frontier mode config

Objective: 让 GitHub 可以不依赖科研主题词。

Modify:

```text
config/sources.yml
```

Add under `github`:

```yaml
mode: frontier
frontier_topic_slug: github_frontier
frontier_days_back: 30
max_frontier_items: 5
frontier_queries:
  - topic:llm stars:>100 archived:false
  - topic:agents stars:>50 archived:false
  - topic:rag stars:>50 archived:false
  - topic:machine-learning stars:>200 archived:false
  - topic:scientific-computing stars:>50 archived:false
  - topic:bioinformatics stars:>50 archived:false
frontier_keywords:
  - llm
  - agent
  - agents
  - rag
  - evaluation
  - benchmark
  - scientific computing
  - bioinformatics
  - research
  - automation
```

Important:

- Do not hardcode date in YAML.
- Code should add `pushed:>{start_date or relative date}` dynamically.

### Task 5: Add GitHub frontier topic

Objective: 单独展示 GitHub 前沿，不归入 AI/神经科学等主题。

Modify:

```text
config/topics.yml
```

Add topic near the end:

```yaml
- slug: github_frontier
  name: GitHub 前沿
  description: 前沿开源项目、AI 工具、科研基础设施和开发者生态趋势。
  max_items: 5
  keywords: []
  exclude_keywords: []
  pubmed_query: null
  arxiv_query: null
```

Risk:

- Empty keywords may interact poorly with `assign_topics_and_scores()` if GitHub collector does not pre-set topics.

Mitigation:

- GitHub frontier collector must set `topics=[frontier_topic_slug]`.
- `assign_topics_and_scores()` preserves pre-set topics because it initializes `matched = list(article.topics)`.

### Task 6: Implement GitHub frontier mode

Objective: 保留旧 topic 模式，新增 frontier 模式。

Modify:

```text
automation/collectors/github.py
```

Top-level function:

```python
def collect_github(...):
    mode = str(source_config.get("mode", "topic")).strip().lower()
    if mode == "frontier":
        return _collect_github_frontier(...)
    return _collect_github_by_topic(...)
```

Frontier behavior:

1. Read `frontier_queries`.
2. Add dynamic pushed date if query does not already include `pushed:`.
3. Search repositories using configured `sort/order` or per-frontier defaults.
4. Convert repo to Article using a synthetic TopicConfig:

```python
TopicConfig(
    slug=frontier_topic_slug,
    name="GitHub 前沿",
    description="...",
    keywords=frontier_keywords,
)
```

5. Score by hotness, not topic relevance.
6. Deduplicate by full_name.
7. Sort by hotness_score.
8. Return max_frontier_items.

Potential helper:

```python
def _frontier_hotness_score(...):
    score = 0
    score += log stars
    score += log forks
    score += recency
    score += release recency
    score += frontier keyword hits
    return round(score, 3)
```

Conservative option:

- Reuse `_repo_to_article()` with synthetic topic and `frontier_keywords`.
- Later refactor only if output quality is poor.

### Task 7: Expand self_check coverage

Objective: 防止回归。

Modify:

```text
scripts/self_check.py
```

Add checks:

1. Highlight source cap:

- Build Digest with 3 NIH high-score items + 2 PubMed/arXiv lower-score items.
- Assert `_pick_highlights()` returns at most 1 NIH.

2. Supplemental source selection:

- Build AI topic with NIH score 9, PubMed score 3, arXiv score 2, GitHub score 5.
- Assert first selected items include primary sources and NIH not overrepresented.

3. GitHub frontier no topic keyword:

- Mock GitHub API response with repo description not containing AI/neuroscience/orthopedics/biomaterials keywords.
- But containing frontier terms or strong stars/recent activity.
- Assert returned article has `topics=["github_frontier"]`.

### Task 8: Run validation

Commands after implementation:

```bash
python3 -m py_compile scripts/daily_digest.py scripts/self_check.py automation/*.py automation/collectors/*.py automation/notifiers/*.py automation/renderers/*.py
python3 scripts/self_check.py
python3 scripts/daily_digest.py --no-fetch --preview --skip-telegram --skip-email --date 2026-01-04
```

If dependencies missing:

```bash
python3 -m pip install -r requirements-automation.txt
```

Avoid network-dependent tests as default. GitHub frontier should be mock-tested in self_check, not require real API.

### Task 9: Review generated digest

Check generated markdown:

```text
data/digests/2026-01-04/digest.md
```

Expected:

- 今日重点不被 NIH 主导。
- GitHub 前沿主题存在（if sample/no-fetch includes GitHub frontier sample）。
- NIH 若存在，作为补充显示，分数/metadata 不混乱。

### Task 10: Git workflow after user approval

If user asks to commit after implementation:

```bash
git status --short
git diff
git add <changed files>
git commit -m "fix: rebalance digest sources and add GitHub frontier mode"
```

Do not push unless explicitly requested.

## Testing / validation details

### Unit-level expectations

1. `_pick_highlights()`:

- Input: 5 items, 3 NIH highest raw relevance, 2 non-NIH lower scores.
- Expected: max 1 NIH in top 3.

2. `select_items_by_topic()`:

- NIH should not crowd out primary sources.
- If only NIH exists, NIH can still fill content so topic is not empty.

3. GitHub frontier:

- Topic keywords irrelevant.
- Repo can be included based on frontier query/hotness.
- Article topic slug is `github_frontier`.

### Integration expectations

1. `scripts/self_check.py` passes.
2. `daily_digest.py --no-fetch --preview` exits 0.
3. Existing output paths still generated:

```text
digest.md
digest.html
digest.json
```

4. Telegram preview remains compact and readable.

## Risks and tradeoffs

### Risk 1: NIH 被降得过低

If NIH is too suppressed, useful funding trend signals may disappear.

Mitigation:

- Keep NIH in theme sections as supplemental.
- Keep metadata.importance_score.
- Only limit highlights and overrepresentation.

### Risk 2: GitHub frontier query quality

GitHub Search API does not provide true trending/star growth. `sort=updated` or `sort=stars` is only proxy.

Mitigation:

- Use stars/forks/release/pushed recency as proxy.
- In future, store daily snapshots to compute star delta.

### Risk 3: GitHub API rate limit

Frontier mode may run multiple queries.

Mitigation:

- Keep `max_pages: 1`.
- Deduplicate early.
- Use `GITHUB_TOKEN` in Actions.
- Limit frontier_queries count.

### Risk 4: Empty keyword topic interaction

`github_frontier` has empty keywords and may be dropped by assignment if not pre-tagged.

Mitigation:

- Collector must set `topics=[github_frontier]`.
- Add self_check for this.

### Risk 5: Existing uncommitted changes

`automation/processing.py` and `scripts/self_check.py` already modified before this plan.

Mitigation:

- Review diff first.
- Avoid blind overwrite.
- If conflicts, ask user.

## Open questions

1. NIH should be excluded from “今日重点” completely, or最多保留 1 条？

Recommended default: 最多 1 条。

2. GitHub 前沿是否应该显示在所有日报中，即使不是科研论文？

Recommended default: 是，作为独立主题 “GitHub 前沿”。

3. GitHub frontier 是否偏 AI 工具，还是也包括科研计算、生信、医学开源工具？

Recommended default: AI 工具 + 科研计算 + 生信/医学开源工具。

4. 是否要把 NIH 改为周报？

Recommended: 暂不做。先在日报中降权。

## Recommended first implementation slice

为了降低风险，建议第一轮只做：

1. `_pick_highlights()` 限制 NIH 最多 1 条。
2. `select_items_by_topic()` 将 NIH 作为 supplemental source。
3. 增加 `github_frontier` topic。
4. GitHub 增加 `mode: frontier`，保留旧 topic 模式。
5. 扩展 `scripts/self_check.py`。

不做：

- 不引入数据库。
- 不做 star 历史增长。
- 不重构 Digest 模型。
- 不新增复杂 UI。
- 不移除 NIH collector。

## Definition of done

完成后应满足：

1. 自动化脚本语法检查通过。
2. self_check 通过。
3. no-fetch preview 能生成 digest。
4. 今日重点不会连续被 NIH 占据。
5. GitHub 前沿可独立展示，不依赖科研主题关键词。
6. 原有 PubMed/arXiv/bioRxiv/medRxiv/RSS 流程不受破坏。
7. 所有改动都可通过 Git diff 清楚审查。
