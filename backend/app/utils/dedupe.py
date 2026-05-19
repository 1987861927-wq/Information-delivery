from app.schemas.article import ArticleRead


def dedupe_articles(articles: list[ArticleRead]) -> list[ArticleRead]:
    seen: set[str] = set()
    result: list[ArticleRead] = []
    for article in articles:
        key = article.doi or article.source_id or article.title.lower().strip()
        if key in seen:
            continue
        seen.add(key)
        result.append(article)
    return result
