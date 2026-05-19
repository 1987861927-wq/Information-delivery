from datetime import UTC, datetime
from xml.etree import ElementTree

import httpx

from app.schemas.article import ArticleRead
from app.services.collectors.base import Collector


class ArxivCollector(Collector):
    source_name = "arXiv"
    base_url = "https://export.arxiv.org/api/query"

    async def search(self, keywords: list[str], days: int = 1) -> list[ArticleRead]:
        if not keywords:
            return []
        query = " OR ".join(f'all:"{keyword}"' for keyword in keywords[:6])
        params = {"search_query": query, "sortBy": "submittedDate", "sortOrder": "descending", "max_results": 20}
        async with httpx.AsyncClient(timeout=30) as client:
            response = await client.get(self.base_url, params=params)
            response.raise_for_status()

        root = ElementTree.fromstring(response.text)
        ns = {"atom": "http://www.w3.org/2005/Atom"}
        articles: list[ArticleRead] = []
        for entry in root.findall("atom:entry", ns):
            arxiv_id = (entry.findtext("atom:id", default="", namespaces=ns) or "").split("/")[-1]
            title = " ".join((entry.findtext("atom:title", default="", namespaces=ns) or "").split())
            abstract = " ".join((entry.findtext("atom:summary", default="", namespaces=ns) or "").split())
            articles.append(
                ArticleRead(
                    id=f"arxiv-{arxiv_id}",
                    source=self.source_name,
                    source_id=arxiv_id,
                    title=title or "Untitled arXiv paper",
                    abstract=abstract,
                    url=entry.findtext("atom:id", default="https://arxiv.org/", namespaces=ns),
                    published_at=datetime.now(UTC),
                    topics=[],
                    relevance_score=0.0,
                    quality_score=0.0,
                    is_preprint=True,
                )
            )
        return articles
