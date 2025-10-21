from sqlalchemy import Column, Integer, String, Text, DateTime, Boolean
from sqlalchemy.ext.declarative import declarative_base

Base = declarative_base()

class Article(Base):
    __tablename__ = 'articles'

    id = Column(Integer, primary_key=True)
    title = Column(String, nullable=False)
    link = Column(String, nullable=False)
    published = Column(DateTime, nullable=False)
    summary = Column(Text, nullable=True)  # 要約カラムを追加
    read_at = Column(DateTime, nullable=True)
    is_favorite = Column(Boolean, default=False, nullable=False)

    def __repr__(self):
        return f"<Article(title={self.title}, link={self.link}, published={self.published})>"
