from datetime import UTC, date, datetime, timedelta

import httpx

from app.schemas.article import ArticleRead
from app.services.collectors.base import Collector


class BiorxivCollector(Collector):
    source_name = "bioRxiv"
    base_url = "https://api.biorxiv.org/details/biorxiv"

    async def search(self, keywords: list[str], days: int = 1) -> list[ArticleRead]:
        end = date.today()
        start = end - timedelta(days=days)
        url = f"{self.base_url}/{start.isoformat()}/{end.isoformat()}"
        async with httpx.AsyncClient(timeout=30) as client:
            response = await client.get(url)
            response.raise_for_status()
            items = response.json().get("collection", [])

        lowered_keywords = [keyword.lower() for keyword in keywords]
        articles: list[ArticleRead] = []
        for item in items:
            text = f"{item.get('title', '')} {item.get('abstract', '')}".lower()
            if lowered_keywords and not any(keyword in text for keyword in lowered_keywords):
                continue
            doi = item.get("doi")
            articles.append(
                ArticleRead(
                    id=f"biorxiv-{doi or item.get('title', '')[:32]}",
                    source=self.source_name,
                    source_id=doi,
                    title=item.get("title") or "Untitled bioRxiv preprint",
                    abstract=item.get("abstract"),
                    url=f"https://www.biorxiv.org/content/{doi}" if doi else "https://www.biorxiv.org/",
                    doi=doi,
                    published_at=datetime.now(UTC),
                    topics=[],
                    relevance_score=0.0,
                    quality_score=0.0,
                    is_preprint=True,
                )
            )
        return articles
