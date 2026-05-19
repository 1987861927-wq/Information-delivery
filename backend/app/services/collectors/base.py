from abc import ABC, abstractmethod

from app.schemas.article import ArticleRead


class Collector(ABC):
    source_name: str

    @abstractmethod
    async def search(self, keywords: list[str], days: int = 1) -> list[ArticleRead]:
        """Search recent articles by keywords."""
