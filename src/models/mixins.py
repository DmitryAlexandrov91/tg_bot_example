from datetime import datetime
from typing import List, Optional

from sqlalchemy import (
    ARRAY,
    Boolean,
    DateTime,
    Integer,
    String,
    Text,
)
from sqlalchemy.orm import (
    Mapped,
    mapped_column,
    validates,
)

from .constants import (
    MAX_LEN_NAME_REFERENCEPOINT,
    MAX_LEN_NAME_ROADMAP,
    MAX_LEN_NAME_TEST,
    TEST_MAX_ANSWERS_COUNT,
    TEST_TIME_RESPOND,
    ReferencePointType,
)


class TimestampMixin:
    """Миксин с полями временных меток."""

    created_at: Mapped[datetime] = mapped_column(
        DateTime,
        default=datetime.utcnow,
        doc='Дата и время создания',
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime,
        default=datetime.utcnow,
        onupdate=datetime.utcnow,
        doc='Дата и время последнего обновления',
    )


class TestMixin:
    """Миксин для модели тестов."""

    name: Mapped[str] = mapped_column(
        String(MAX_LEN_NAME_TEST), nullable=False, unique=True)
    time_respond: Mapped[int] = mapped_column(
        Integer, default=TEST_TIME_RESPOND)


class QuestionMixin:
    """Миксин для модели ответов на тесты."""

    text_question: Mapped[str] = mapped_column(Text, nullable=False)
    correct_answer: Mapped[int] = mapped_column(Integer, nullable=False)
    answers: Mapped[list[str]] = mapped_column(ARRAY(String), nullable=False)

    @validates("answers")
    def validate_answers_count(
        self,
        key: str,
        answers: List[str],
    ) -> List[str]:
        """Проверяет, количество вариантов ответов в тесте."""
        if len(answers) > TEST_MAX_ANSWERS_COUNT:
            raise ValueError(
                f'Вопрос не может содержать более '
                f'{TEST_MAX_ANSWERS_COUNT} ответов.',
            )
        return answers


class NotificationMixin:
    """Миксин для модели уведомлений."""

    text: Mapped[str] = mapped_column(Text, nullable=False)
    need_feedback: Mapped[bool] = mapped_column(Boolean, default=False)
    feedbacks: Mapped[list[str]] = mapped_column(ARRAY(String))
    links: Mapped[list[str]] = mapped_column(ARRAY(String))
    servise_notes: Mapped[list[str]] = mapped_column(
        ARRAY(String))


class FeedbackRequestMixin:
    """Миксин для модели запросов обратной связи."""

    text: Mapped[str] = mapped_column(Text, nullable=False)


class RoadMapMixin:
    """Миксин для модели дорожных карт."""

    name: Mapped[str] = mapped_column(
        String(MAX_LEN_NAME_ROADMAP), nullable=False, unique=True)
    description: Mapped[Optional[str]] = mapped_column(Text)


class ReferencePointMixin:
    """Миксин для модели контрольных точек."""

    name: Mapped[str] = mapped_column(
        String(MAX_LEN_NAME_REFERENCEPOINT), nullable=False, unique=True)
    point_type: Mapped[str] = mapped_column(
        default=ReferencePointType.NOTIFICATION)
    is_blocked: Mapped[bool] = mapped_column(Boolean, default=False)
    auto_closing: Mapped[bool] = mapped_column(Boolean, default=True)
    order_execution: Mapped[int] = mapped_column(Integer, nullable=False)
