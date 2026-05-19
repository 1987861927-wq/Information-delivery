from datetime import UTC, datetime
from urllib.parse import quote_plus

import httpx

from app.core.config import settings
from app.schemas.article import ArticleRead
from app.services.collectors.base import Collector


class PubMedCollector(Collector):
    source_name = "PubMed"
    base_url = "https://eutils.ncbi.nlm.nih.gov/entrez/eutils"

    async def search(self, keywords: list[str], days: int = 1) -> list[ArticleRead]:
        if not keywords:
            return []

        query = " OR ".join(f'"{keyword}"' for keyword in keywords[:8])
        params = {
            "db": "pubmed",
            "term": query,
            "retmode": "json",
            "retmax": "20",
            "sort": "pub date",
            "reldate": str(days),
            "datetype": "pdat",
            "email": settings.ncbi_email,
        }
        if settings.ncbi_api_key:
            params["api_key"] = settings.ncbi_api_key

        async with httpx.AsyncClient(timeout=20) as client:
            response = await client.get(f"{self.base_url}/esearch.fcgi", params=params)
            response.raise_for_status()
            ids = response.json().get("esearchresult", {}).get("idlist", [])

        return [
            ArticleRead(
                id=f"pubmed-{pmid}",
                source=self.source_name,
                source_id=pmid,
                title=f"PubMed article {pmid}",
                abstract=None,
                url=f"https://pubmed.ncbi.nlm.nih.gov/{quote_plus(pmid)}/",
                published_at=datetime.now(UTC),
                topics=[],
                relevance_score=0.0,
                quality_score=0.0,
                is_preprint=False,
            )
            for pmid in ids
        ]
