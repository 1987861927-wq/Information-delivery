import asyncio

from app.services.collectors import ArxivCollector, BiorxivCollector, MedrxivCollector, PubMedCollector
from app.services.summarizers import LLMSummarizer
from app.services.topic_service import topic_service


async def run_daily_pipeline(topic_slug: str | None = None) -> dict[str, int]:
    keywords = topic_service.get_keywords(topic_slug)
    collectors = [PubMedCollector(), BiorxivCollector(), MedrxivCollector(), ArxivCollector()]
    summarizer = LLMSummarizer()

    collected = []
    for collector in collectors:
        try:
            collected.extend(await collector.search(keywords=keywords, days=1))
        except Exception:
            # TODO: 替换为结构化日志和告警。
            continue

    summarized = 0
    for article in collected[:20]:
        await summarizer.summarize(article)
        summarized += 1

    return {"collected": len(collected), "summarized": summarized}


if __name__ == "__main__":
    result = asyncio.run(run_daily_pipeline())
    print(result)
