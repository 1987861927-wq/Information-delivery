from sqlalchemy import String, Text
from sqlalchemy.orm import Mapped, mapped_column

from app.db.session import Base


class Topic(Base):
    __tablename__ = "topics"

    id: Mapped[int] = mapped_column(primary_key=True, index=True)
    slug: Mapped[str] = mapped_column(String(80), unique=True, index=True)
    name: Mapped[str] = mapped_column(String(120))
    description: Mapped[str] = mapped_column(Text)
