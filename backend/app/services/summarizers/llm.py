from app.core.config import settings
from app.schemas.article import ArticleRead
from app.schemas.summary import StructuredSummary


class LLMSummarizer:
    """LLM 摘要服务骨架。

    当前提供无 API Key 时的 deterministic fallback，后续可接入 OpenAI/Claude/Gemini。
    """

    async def summarize(self, article: ArticleRead) -> StructuredSummary:
        if not settings.openai_api_key:
            return StructuredSummary(
                one_sentence=f"这是一篇来自 {article.source} 的候选内容，主题相关性需要进一步模型判断。",
                research_question="待通过 LLM 提取研究问题。",
                methods="待通过 LLM 提取方法亮点。",
                key_findings=["待通过 LLM 提取核心发现。"],
                value="待通过 LLM 评估科研、临床或工程价值。",
                limitations="当前摘要为占位版本，尚未进行事实校验。",
                audience=["研究者"],
            )

        # TODO: 接入真实 LLM 调用，并要求模型输出严格 JSON。
        return StructuredSummary(
            one_sentence=f"{article.title} 的中文结构化摘要待生成。",
            research_question="待生成。",
            methods="待生成。",
            key_findings=["待生成。"],
            value="待生成。",
            limitations="待生成。",
            audience=["研究者"],
        )
