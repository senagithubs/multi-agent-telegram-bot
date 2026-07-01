"""
core/database.py
----------------
Veritabanı katmanı (SQLAlchemy ORM).
Kullanıcıları ve konuşma geçmişini saklar. LLM ajanlarının bağlam
(context) hafızası bu geçmişten beslenir.

Neden ORM? Ham SQL yerine ORM kullanmak kod enjeksiyonunu önler ve
farklı veritabanları (SQLite geliştirmede, PostgreSQL üretimde) arasında
geçişi kolaylaştırır.
"""

from datetime import datetime, timezone

from sqlalchemy import (
    create_engine, String, Integer, DateTime, Text, ForeignKey,
)
from sqlalchemy.orm import (
    DeclarativeBase, Mapped, mapped_column, relationship, sessionmaker,
)


class Base(DeclarativeBase):
    pass


class User(Base):
    __tablename__ = "users"

    id: Mapped[int] = mapped_column(primary_key=True)
    telegram_id: Mapped[int] = mapped_column(Integer, unique=True, index=True)
    username: Mapped[str | None] = mapped_column(String(255), nullable=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime, default=lambda: datetime.now(timezone.utc)
    )

    messages: Mapped[list["Message"]] = relationship(
        back_populates="user", cascade="all, delete-orphan"
    )


class Message(Base):
    __tablename__ = "messages"

    id: Mapped[int] = mapped_column(primary_key=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id"), index=True)
    role: Mapped[str] = mapped_column(String(20))   # "user" veya "assistant"
    agent_name: Mapped[str | None] = mapped_column(String(50), nullable=True)
    content: Mapped[str] = mapped_column(Text)
    created_at: Mapped[datetime] = mapped_column(
        DateTime, default=lambda: datetime.now(timezone.utc)
    )

    user: Mapped["User"] = relationship(back_populates="messages")


class Database:
    """Veritabanı işlemlerini kapsülleyen basit servis."""

    def __init__(self, database_url: str):
        # SQLite için thread güvenliği ayarı
        connect_args = {}
        if database_url.startswith("sqlite"):
            connect_args = {"check_same_thread": False}
        self.engine = create_engine(database_url, connect_args=connect_args)
        self.SessionLocal = sessionmaker(bind=self.engine)
        Base.metadata.create_all(self.engine)

    def get_or_create_user(self, telegram_id: int, username: str | None) -> User:
        with self.SessionLocal() as session:
            user = (
                session.query(User)
                .filter_by(telegram_id=telegram_id)
                .first()
            )
            if user is None:
                user = User(telegram_id=telegram_id, username=username)
                session.add(user)
                session.commit()
                session.refresh(user)
            return user

    def save_message(
        self, telegram_id: int, role: str, content: str,
        agent_name: str | None = None,
    ) -> None:
        with self.SessionLocal() as session:
            user = (
                session.query(User)
                .filter_by(telegram_id=telegram_id)
                .first()
            )
            if user is None:
                user = User(telegram_id=telegram_id, username=None)
                session.add(user)
                session.flush()
            session.add(Message(
                user_id=user.id, role=role,
                content=content, agent_name=agent_name,
            ))
            session.commit()

    def get_recent_history(
        self, telegram_id: int, limit: int = 10,
    ) -> list[dict]:
        """Son N mesajı kronolojik sırada döndürür (LLM bağlamı için)."""
        with self.SessionLocal() as session:
            user = (
                session.query(User)
                .filter_by(telegram_id=telegram_id)
                .first()
            )
            if user is None:
                return []
            rows = (
                session.query(Message)
                .filter_by(user_id=user.id)
                .order_by(Message.created_at.desc())
                .limit(limit)
                .all()
            )
            # En yeniden en eskiye geldi; LLM için ters çevir
            return [
                {"role": m.role, "content": m.content}
                for m in reversed(rows)
            ]
