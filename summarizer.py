import openai
from typing import List, Optional, Dict, Any, Tuple
from sqlalchemy.orm import Session, joinedload
from database import get_db, Article
from config import settings
import logging
from datetime import datetime
import requests
import tempfile
import os


logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class ArticleSummarizer:
    def __init__(self):
        openai.api_key = settings.openai_api_key
        self.client = openai.OpenAI(api_key=settings.openai_api_key)

    def create_ochiai_summary(self, article: Article) -> str:
        """
        Create summary using Ochiai format (落合フォーマット) and parse into sections
        """
        prompt = f"""
以下の記事を落合フォーマットで要約してください。落合フォーマットは以下の6つの観点で構成されます：

1. どんなもの？
2. 先行研究と比べてどこがすごい？
3. 技術や手法のキモはどこ？
4. どうやって有効だと検証した？
5. 議論はある？
6. 次読むべき論文は？

記事情報：
タイトル: {article.title}
URL: {article.link}

内容:
{article.description[: settings.article_description_limit]}  # Limit content to avoid token limits

要約は日本語で、各観点について簡潔にまとめてください。技術的な内容の場合は専門用語も適切に使用して。
必ず各セクションを「1. どんなもの？」のように番号付きで明確に区切って。あと書き言葉で書いて。
"""

        try:
            response = self.client.chat.completions.create(
                model=settings.gpt_model,
                messages=[
                    {
                        "role": "system",
                        "content": "あなたは研究論文や技術記事の要約を専門とするAIアシスタントです。落合フォーマットに従って、正確な要約を作成してください。",
                    },
                    {"role": "user", "content": prompt},
                ],
                temperature=settings.openai_temperature,
            )

            summary = response.choices[0].message.content.strip()

            # 各セクションを分割して保存
            self._parse_and_save_sections(article, summary)

            return summary

        except Exception as e:
            logger.error(f"Error creating summary for article {article.id}: {e}")
            return f"要約の生成に失敗しました: {str(e)}"

    def _parse_and_save_sections(self, article: Article, summary: str) -> None:
        """
        Parse the Ochiai format summary into separate sections and save to article
        """
        try:
            # 正規表現パターンを定義
            import re

            # 各セクションのパターン
            patterns = {
                "top_summary": r"1\.\s*どんなもの？\s*(.*?)(?=2\.\s*先行研究|$)",
                "comparison": r"2\.\s*先行研究と比べてどこがすごい？\s*(.*?)(?=3\.\s*技術や手法|$)",
                "technique": r"3\.\s*技術や手法のキモはどこ？\s*(.*?)(?=4\.\s*どうやって有効|$)",
                "validation": r"4\.\s*どうやって有効だと検証した？\s*(.*?)(?=5\.\s*議論|$)",
                "discussion": r"5\.\s*議論はある？\s*(.*?)(?=6\.\s*次読むべき|$)",
                "next_papers": r"6\.\s*次読むべき論文は？\s*(.*?)(?=$)",
            }

            # 各セクションを抽出して保存
            for field, pattern in patterns.items():
                match = re.search(pattern, summary, re.DOTALL)
                if match:
                    content = match.group(1).strip()
                    setattr(article, field, content)
                else:
                    # マッチしない場合は空文字列を設定
                    setattr(article, field, "")

        except Exception as e:
            logger.error(
                f"Error parsing summary sections for article {article.id}: {e}"
            )

    def summarize_unsummarized_articles(self) -> int:
        """Summarize all articles that don't have summaries yet"""
        db = next(get_db())
        try:
            # Get all unsummarized articles
            articles = db.query(Article).filter(Article.is_summarized == False).all()

            if not articles:
                logger.info("No unsummarized articles found")
                return 0

            summarized_count = 0
            for article in articles:
                try:
                    summary = self.create_ochiai_summary(article)
                    article.summary = summary
                    article.is_summarized = True
                    summarized_count += 1
                    logger.info(
                        f"Created summary for article {article.id}: {article.title}"
                    )
                except Exception as e:
                    logger.error(f"Error summarizing article {article.id}: {e}")
                    continue

            db.commit()
            logger.info(f"Successfully summarized {summarized_count} articles")
            return summarized_count

        except Exception as e:
            db.rollback()
            logger.error(f"Error in summarize_unsummarized_articles: {e}")
            return 0
        finally:
            db.close()


if __name__ == "__main__":
    summarizer = ArticleSummarizer()
    summarizer.summarize_unsummarized_articles()
