#!/usr/bin/env python3
from __future__ import annotations

import subprocess
import sys
from datetime import date
from pathlib import Path
from typing import Any

PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))


class FakeResponse:
    def __init__(self, status_code: int, data: dict[str, Any] | None = None, text: str = "") -> None:
        self.status_code = status_code
        self._data = data or {}
        self.text = text

    def json(self) -> dict[str, Any]:
        return self._data

    def raise_for_status(self) -> None:
        if self.status_code >= 400:
            raise RuntimeError(f"fake HTTP {self.status_code}")


def run(command: list[str]) -> None:
    print("$", " ".join(command))
    subprocess.run(command, cwd=PROJECT_ROOT, check=True)


def main() -> int:
    run_mock_collector_checks()
    run([sys.executable, "scripts/daily_digest.py", "--no-fetch", "--preview", "--skip-telegram", "--skip-email", "--date", "2026-01-01"])
    run(
        [
            sys.executable,
            "scripts/daily_digest.py",
            "--no-fetch",
            "--preview",
            "--skip-telegram",
            "--skip-email",
            "--date",
            "2026-01-02",
            "--top-journal-mode",
            "push",
            "--min-impact-factor",
            "10",
        ]
    )
    expected = PROJECT_ROOT / "data" / "digests" / "2026-01-01" / "digest.md"
    expected_top_journal = PROJECT_ROOT / "data" / "digests" / "2026-01-02" / "digest.md"
    for path in (expected, expected_top_journal):
        if not path.exists():
            raise SystemExit(f"自检失败：未生成 {path}")
    markdown = expected.read_text(encoding="utf-8")
    for needle in ("GitHub: sample/biomedical-llm-toolkit", "NIH Grant: AI-enabled biomarkers for neurodegeneration", "关键元数据", "评分："):
        if needle not in markdown:
            raise SystemExit(f"自检失败：日报缺少 {needle}")
    print(f"自检通过：已生成 {expected} 和 {expected_top_journal}，并包含 GitHub/NIH 样例")
    return 0


def run_mock_collector_checks() -> None:
    from automation.collectors import github as github_collector
    from automation.collectors import nih_reporter as nih_collector
    from automation.models import TopicConfig

    topic = TopicConfig(
        slug="ai",
        name="人工智能",
        description="AI for Science",
        keywords=["artificial intelligence", "large language model", "biomedical"],
    )
    start = date(2026, 1, 1)
    end = date(2026, 1, 2)

    original_github_get = github_collector._github_get
    original_reporter_post = nih_collector._post_reporter
    try:
        github_item = {
            "full_name": "sample/biomedical-llm-toolkit",
            "description": "Biomedical large language model toolkit for literature triage.",
            "html_url": "https://github.com/sample/biomedical-llm-toolkit",
            "updated_at": "2026-01-02T00:00:00Z",
            "created_at": "2025-01-01T00:00:00Z",
            "pushed_at": "2026-01-02T00:00:00Z",
            "stargazers_count": 1280,
            "forks_count": 120,
            "watchers_count": 1280,
            "open_issues_count": 18,
            "language": "Python",
            "topics": ["biomedical-nlp", "llm", "literature-triage"],
            "owner": {"login": "sample"},
        }

        def fake_github_get(path, headers, params=None, timeout=30):  # noqa: ANN001, ANN202
            if path == "/search/repositories":
                return FakeResponse(200, {"items": [github_item, github_item]})
            if path.endswith("/releases/latest"):
                return FakeResponse(404, {})
            return FakeResponse(500, {}, "unexpected path")

        github_collector._github_get = fake_github_get
        github_articles = github_collector.collect_github(
            [topic],
            start,
            end,
            {
                "enabled": True,
                "max_results_per_topic": 5,
                "per_page": 2,
                "max_pages": 1,
                "min_score": 0,
                "min_stars": 0,
                "include_latest_release": True,
                "keywords": ["biomedical"],
            },
        )
        if len(github_articles) != 1 or github_articles[0].source != "GitHub" or github_articles[0].metadata.get("stars") != 1280:
            raise SystemExit("自检失败：GitHub mock collector 未正确去重或映射字段")

        github_collector._github_get = lambda *args, **kwargs: FakeResponse(403, {}, "rate limit")
        if github_collector.collect_github([topic], start, end, {"enabled": True}):
            raise SystemExit("自检失败：GitHub rate limit mock 应返回空列表")

        github_collector._github_get = lambda *args, **kwargs: None
        if github_collector.collect_github([topic], start, end, {"enabled": True}):
            raise SystemExit("自检失败：GitHub network failure mock 应返回空列表")

        nih_item = {
            "appl_id": 123456,
            "project_num": "R01-SAMPLE-0001",
            "project_title": "AI-enabled biomarkers for neurodegeneration",
            "abstract_text": "This project develops biomedical artificial intelligence biomarkers for neurodegeneration.",
            "agency_ic_admin": {"abbreviation": "NIA"},
            "agency_ic_fundings": [],
            "principal_investigators": [{"full_name": "Jane Doe"}],
            "organization": {"org_name": "Sample University"},
            "fiscal_year": 2026,
            "project_start_date": "2026-01-01",
            "project_end_date": "2030-12-31",
            "award_amount": 750000,
            "project_detail_url": "https://reporter.nih.gov/project-details/123456",
            "terms": [{"term": "biomedical artificial intelligence"}, {"term": "neurodegeneration"}],
        }

        nih_collector._post_reporter = lambda payload: FakeResponse(200, {"results": [nih_item, nih_item]})
        nih_articles = nih_collector.collect_nih_reporter(
            [topic],
            start,
            end,
            {"enabled": True, "max_results_per_topic": 5, "limit": 2, "max_pages": 1, "min_score": 0},
        )
        if len(nih_articles) != 1 or nih_articles[0].source != "NIH RePORTER" or nih_articles[0].metadata.get("award_amount") != 750000:
            raise SystemExit("自检失败：NIH RePORTER mock collector 未正确去重或映射字段")

        nih_collector._post_reporter = lambda payload: FakeResponse(200, {"results": []})
        if nih_collector.collect_nih_reporter([topic], start, end, {"enabled": True}):
            raise SystemExit("自检失败：NIH RePORTER empty mock 应返回空列表")

        nih_collector._post_reporter = lambda payload: None
        if nih_collector.collect_nih_reporter([topic], start, end, {"enabled": True}):
            raise SystemExit("自检失败：NIH RePORTER network failure mock 应返回空列表")
    finally:
        github_collector._github_get = original_github_get
        nih_collector._post_reporter = original_reporter_post
    print("自检通过：GitHub/NIH RePORTER mock collector 降级、去重和字段映射正常")


if __name__ == "__main__":
    raise SystemExit(main())
